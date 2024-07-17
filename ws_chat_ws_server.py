import asyncio
import logging
from datetime import datetime

import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from aiofile import async_open
from aiopath import AsyncPath

from main import query_manager
from handlers import gpt_handler

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def logger(self, name: str, query: str) -> None:
        apath = AsyncPath('exchange_logger.txt')
        async with async_open(apath, 'a') as file:
            await file.write(f'{datetime.now()} user {name} searched "{query}"\n')

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message.startswith('exchange'):

                await self.logger(ws.name, message)
                response = []
                try:
                    args = message.split(' ')
                    if len(args) == 1:
                        response = await query_manager(1, [])
                    elif len(args) == 2 and int(args[1]) <= 10:
                        response = await query_manager(int(args[1]), [])
                    elif int(args[1]) > 10:
                        raise ValueError('You can see maximum 10 days')
                    else:
                        response = await query_manager(int(args[1]), args[2:])
                    if not response:
                        raise ValueError('The currency is not supported')

                except ValueError as err:
                    await self.send_to_clients(f"{ws.name}: The example of currency exchange pattern:"
                                               f" 'exchange <days> <currencies>' -> 'exchange 3 EUR USD'")
                    await self.send_to_clients(f'{err}')

                await self.send_exchange_currencies_response(response)

            elif message.startswith('gpt'):
                await self.send_to_clients(f"{ws.name}: {message}")
                await self.send_to_clients(await gpt_handler(message))

            else:
                await self.send_to_clients(f"{ws.name}: {message}")

    async def send_exchange_currencies_response(self, response: list):
        for line in response:
            for date, currency in line.items():
                for currency_name, currency_values in currency.items():
                    try:
                        response_to_chat = (
                            f'{date}: {currency_name} - the price to buy: {currency_values["sale"]} UAH,'
                            f' and to sell: {currency_values["purchase"]} UAH')
                        await self.send_to_clients(f"{response_to_chat}")
                    except TypeError as err:
                        await self.send_to_clients(f"{currency_name}: {err}")



async def main():
    try:
        server = Server()
        async with websockets.serve(server.ws_handler, '0.0.0.0', 8080):
            await asyncio.Future()  # run forever
    except asyncio.exceptions.CancelledError:
        pass


if __name__ == '__main__':
    asyncio.run(main())

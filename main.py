import logging
import asyncio
import sys
from datetime import datetime, timedelta
from typing import Any

import aiohttp

import ssl
import certifi

logging.basicConfig(level=logging.DEBUG)

PRIVAT_BANK_CURRENCIES = ['CHF', 'EUR', 'GBP', 'PLZ', 'SEK', 'UAH', 'USD', 'XAU', 'CAD']


async def take_currency(currency: str, date: str) -> dict[Any, dict[str, Any]]:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.privatbank.ua/p24api/exchange_rates?json&date=' + date, ssl=ssl_context) as response:

            resp_json = await response.json()

            logging.info(f'Started courutine: {currency}')

            for n in resp_json['exchangeRate']:
                if n['currency'] == currency:
                    try:
                        return {'sale': n['saleRate'],
                                'purchase': n['purchaseRate']}
                    except KeyError:
                        return {'sale': n['saleRateNB'],
                                'purchase': n['purchaseRateNB']}


async def query_manager(main_period: int, currencies: list) -> list:
    today = datetime.now()
    if not currencies:
        currencies = ['USD', 'EUR']

    output = []
    for n in range(main_period):
        date_obj = today - timedelta(days=n)
        date = date_obj.strftime("%d.%m.%Y")
        currency_dict = {}
        for c in currencies:
            if c.upper() in PRIVAT_BANK_CURRENCIES:
                currency_dict[c.upper()] = await take_currency(c.upper(), date)
            else:
                output = [f'Currency {c} is not supported']
                logging.debug(output)
                raise ValueError("Supported currencies - ['CHF', 'EUR', 'GBP', 'PLZ', 'SEK', 'UAH', 'USD', 'XAU', 'CAD']")

        logging.debug(f'Currency dict --- {currency_dict}')
        output.append({date: currency_dict})

    logging.info(f'Output --- {output}')
    return output


if __name__ == '__main__':
    period = int(sys.argv[1])
    add_currencies = sys.argv[2:]
    normalise_cur = []
    for c in add_currencies:
        normalise_cur.append(c.upper())
    asyncio.run(query_manager(period, normalise_cur))

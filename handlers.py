import os
import requests
import asyncio
import aiohttp

import os
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + os.getenv('OPENAI_API_KEY', ''),
}

print(HEADERS)


async def gpt_handler(message: str) -> str:
    json_data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'user',
                'content': message,
            },
            {
                "role": "assistant",
                "content": "\n\nYou are helpful assistant which answer the user's questions"
            }
        ],
        'temperature': 0.7,
    }
    async with aiohttp.ClientSession() as session:

        async with session.post('https://api.openai.com/v1/chat/completions', headers=HEADERS,
                                json=json_data, ssl=False) as response:

            print("Status:", response.status)
            answer = await response.json()
            return answer['choices'][0]['message']['content']

if __name__ == '__main__':
    print(asyncio.run(gpt_handler('tell a joke')))

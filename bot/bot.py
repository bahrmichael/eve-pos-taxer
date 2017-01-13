import json
from pprint import pprint

import discord
import asyncio
import requests

client = discord.Client()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    if message.content.startswith('!test'):
        print(message.channel)
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')
    elif message.content.startswith('!errors'):
        tmp = await client.send_message(message.channel, 'Reading the dark books ...')
        response = requests.get('http://hordedelivery.com:11000/errors?authkey=7NbPOJCytgbI0KRGes6J')
        json_data = json.loads(response.text)
        corp_ids = set([])
        for entry in json_data:
            corp_ids.add(entry['corpId'])
        await client.edit_message(tmp, 'CorpIds with error: %s' % json.dumps(list(corp_ids)))

client.run('MjY5MjI1ODUxNzQzMjQwMTkz.C1mPqQ._s96H308u9FDL00fCqGWIB3z6kY')

import json
from pprint import pprint

import discord
import asyncio
import requests
import os

client = discord.Client()


async def my_background_task():
    await client.wait_until_ready()
    counter = 0
    channel = discord.Object(id='general')
    while not client.is_closed:
        counter += 1
        # await client.send_message(channel, counter)
        print(counter)
        await asyncio.sleep(2)  # task runs every 60 seconds


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    channel_name = os.environ['CHANNEL']
    notifiees = os.environ['NOTIFIEES']

    ch = None
    for channel in client.get_all_channels():
        if str(channel).lower() == channel_name.lower():
            ch = channel
            break

    if ch is None:
        print("ERROR: Could not find channel " + channel_name)
        return

    members = []
    for member in client.get_all_members():
        if str(member) in notifiees:
            members.append(member)
        else:
            print("not in list " + str(member))

    if len(members) > 0:
        target = members[0]
        response = target.mention + ", your message."
        await client.send_message(ch, response)


client.run('MjY5MjI1ODUxNzQzMjQwMTkz.C1mPqQ._s96H308u9FDL00fCqGWIB3z6kY')

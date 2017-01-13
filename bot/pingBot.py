import os

import discord
import requests
import json

client = discord.Client()


def lambda_handler(event, context):
    # message = event['Records'][0]['Sns']['Message']
    # print("SNS Message: " + message)
    # if message == "test-error":
    client.run('MjY5MjI1ODUxNzQzMjQwMTkz.C1mPqQ._s96H308u9FDL00fCqGWIB3z6kY')
    return "done"

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    corp_ids = await find_corp_ids()

    channel_name = os.environ['CHANNEL']
    notifiees = os.environ['NOTIFIEES']

    ch = await find_channel(channel_name)

    if ch is None:
        print("ERROR: Could not find channel " + channel_name)
        return

    members = await find_members(notifiees)

    if len(members) > 0 and len(corp_ids) >= 0:
        target = members[0]
        response = target.mention + ' CorpIds with error: %s' % json.dumps(list(corp_ids))
        await client.send_message(ch, response)

    await client.close()


async def find_corp_ids():
    response = requests.get('http://hordedelivery.com:11000/errors?authkey=7NbPOJCytgbI0KRGes6J')
    json_data = json.loads(response.text)
    corp_ids = set([])
    for entry in json_data:
        corp_ids.add(entry['corpId'])
    return corp_ids


async def find_members(notifiees):
    members = []
    for member in client.get_all_members():
        if str(member) in notifiees:
            members.append(member)
        else:
            print("%s is not in the list of notifiees" % str(member))
    return members


async def find_channel(channel_name):
    ch = None
    for channel in client.get_all_channels():
        if str(channel) == channel_name:
            ch = channel
            break
    return ch

lambda_handler('ct', 'ct')

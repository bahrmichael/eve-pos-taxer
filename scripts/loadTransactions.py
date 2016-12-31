import xml.etree.ElementTree
from datetime import datetime

import requests
import os

from classes.mongoProvider import MongoProvider

endpoint = "/corp/WalletJournal.xml.aspx"


def main():
    print "## Load transactions"
    print "establishing connection ..."
    client = MongoProvider().provide()

    for corp in client.corporations.find():
        print "processing corp %s" % corp['corpName']
        load_for_corp(client, corp['key'], corp['vCode'], corp['corpId'])


def load_for_corp(client, key_id, v_code, corp_id):
    verification = "keyID=%d&vCode=%s" % (key_id, v_code)
    url = "https://api.eveonline.com%s?%s" % (endpoint, verification)
    r = requests.get(url)
    data = r.content
    e = xml.etree.ElementTree.fromstring(data)
    try:
        rows = e[1][0]
    except IndexError:
        print "Could not access the wallet api for corpId " + str(corp_id)
        post = {
            'timestamp': datetime.now(),
            'message': 'Could not access the WalletJournal API',
            'script': 'loadTransactions',
            'corpId': corp_id
        }
        client.error_log.insert_one(post)
        return

    transaction_journal = client.transactionjournal

    recipient = os.environ['EVE_POS_TAX_RECIPIENT']

    for row in rows:
        # check if it is a donation to a given player name
        if row.get('ownerName2') == recipient:
            post = {
                "transactionId": long(row.get('refID')),
                "date": row.get('date'),
                "corpId": long(corp_id),
                "amount": -1 * float(row.get('amount'))
            }
            found = transaction_journal.find_one({"transactionId": post['transactionId']})
            if found is None:
                transaction_journal.insert_one(post)
                print str(post['transactionId']) + " added"
            else:
                print str(post['transactionId']) + " already exists"

if __name__ == "__main__":
    main()

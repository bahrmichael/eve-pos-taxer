import os
from datetime import datetime

from classes.apiWrapper import ApiWrapper
from classes.mongoProvider import MongoProvider

endpoint = "/corp/WalletJournal.xml.aspx"
recipient = os.environ['EVE_POS_TAX_RECIPIENT']


def main():
    print "## Load transactions"
    print "establishing connection ..."
    client = MongoProvider().provide()

    for corp in client.corporations.find():
        print "processing corp %s" % corp['corpName']
        load_for_corp(client, corp['key'], corp['vCode'], corp['corpId'])


def load_for_corp(mongo_client, key_id, v_code, corp_id):
    transaction_journal = mongo_client.transactionjournal

    api_result = ApiWrapper(endpoint, key_id, v_code).call(None)
    if api_result is None:
        print "Could not access the wallet api for corpId " + str(corp_id)
        post = {
            'timestamp': datetime.now(),
            'message': 'Could not access the WalletJournal API',
            'script': 'loadTransactions',
            'corpId': corp_id
        }
        mongo_client.error_log.insert_one(post)
        return

    for row in api_result[0]:
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

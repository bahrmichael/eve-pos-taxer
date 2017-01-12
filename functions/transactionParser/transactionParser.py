# -*- coding: utf-8 -*-

import os

from datetime import datetime

from eveapimongo import ApiWrapper, MongoProvider

print('Loading function')


def lambda_handler(event, context):
    TransactionParser().main()
    return "done"


class TransactionParser:

    endpoint = "/corp/WalletJournal.xml.aspx"
    has_new_transaction = None

    def main(self):
        print("loading corporations ...")
        for corp in MongoProvider().find('corporations'):
            print("processing corp %s" % corp['corpName'])
            self.process_corp(corp['key'], corp['vCode'], corp['corpId'])

        if self.has_new_transaction:
            self.notify_aws_sns()

    def notify_aws_sns(self):
        import boto3
        boto3.client('sns').publish(
            TargetArn=os.environ['EVE_POS_SNS_QUEUE'],
            Message='transaction-added'
        )

    def process_corp(self, key_id, v_code, corp_id):
        api_result = ApiWrapper(self.endpoint, key_id, v_code).call(None)
        if api_result is None:
            self.handle_error(corp_id)
            return

        for row in api_result[0]:
            # check if it is a donation to a given player name
            self.process_transaction(corp_id, row)

    def process_transaction(self, corp_id, row):
        if self.is_target_recipient(row):
            post = self.build_entry(corp_id, row)
            found = MongoProvider().find_one('transactionjournal', {"transactionId": post['transactionId']})
            if found is None:
                MongoProvider().insert('transactionjournal', post)
                self.has_new_transaction = "true"
                print(str(post['transactionId']) + " added")
            else:
                print(str(post['transactionId']) + " already exists")

    def build_entry(self, corp_id, row):
        return {
            "transactionId": int(row.get('refID')),
            "date": row.get('date'),
            "corpId": int(corp_id),
            "amount": -1 * float(row.get('amount'))
        }

    def is_target_recipient(self, row):
        return row.get('ownerName2') == self.get_tax_recipient()

    def handle_error(self, corp_id):
        print("Could not access the wallet api for corpId " + str(corp_id))
        post = {
            'timestamp': self.date_now(),
            'message': 'Could not access the WalletJournal API',
            'script': 'loadTransactions',
            'corpId': corp_id
        }
        MongoProvider().insert('error_log', post)

    def date_now(self):
        return datetime.now()

    def get_tax_recipient(self):
        return os.environ['EVE_POS_TAX_RECIPIENT']

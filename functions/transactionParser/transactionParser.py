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
            if 'failedAt' not in corp:
                self.process_corp(corp['key'], corp['vCode'], corp['corpId'])
            else:
                print("The corp %s has previously failed and will not be parsed." % corp['corpName'])

        if self.has_new_transaction:
            self.notify_aws_sns('EVE_POS_SNS_QUEUE', 'transaction-added')

    def notify_aws_sns(self, topic_variable, message):
        import boto3
        boto3.client('sns').publish(
            TargetArn=os.environ[topic_variable],
            Message=message
        )

    def process_corp(self, key_id, v_code, corp_id):
        account_keys = [1000, 1001, 1002, 1003, 1004, 1005, 1006]
        row_count = 2560
        for account_key in account_keys:
            api_result = ApiWrapper(self.endpoint, key_id, v_code).call(
                {'accountKey': account_key, 'rowCount': row_count})
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

        corp = MongoProvider().find_one('corporations', {'corpId': corp_id})
        corp['failedAt'] = self.date_now()
        self.update_corp(corp)

        self.notify_aws_sns('EVE_POS_SNS_ERROR', 'Error parsing API for %s' % corp['corpName'])

    def update_corp(self, corp):
        MongoProvider().provide().get_collection('corporations').replace_one({'corpId': corp['corpId']}, corp)

    def date_now(self):
        return datetime.now()

    def get_tax_recipient(self):
        return os.environ['EVE_POS_TAX_RECIPIENT']

from pprint import pprint

from eveapimongo import MongoProvider
from pymongo.errors import BulkWriteError

POS_DAY_FEE = 2000000


def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message']
    print("SNS Message: " + message)
    if message == "deposits-built":
        BalanceJournalBuilder().main()
        return "done"


class Balance:
    def __init__(self, date, amount):
        self.date = date
        self.amount = amount

    def __repr__(self):
        return repr((self.date, self.amount))


class BalanceJournalBuilder:

    def get_negative_days(self,balance_array):
        reversed_balances = sorted(balance_array, key=lambda x: x.date, reverse=True)
        negative_count = 0
        for balance in reversed_balances:
            if balance.amount < 0:
                negative_count += 1
            else:
                break
        return negative_count

    def get_corp_name(self,corp_id, mongo_client):
        result = mongo_client.corporations.find_one({'corpId': corp_id})
        print(corp_id)
        if result:
            return result['corpName']
        else:
            return "n/a"

    def has_entry_for_date(self,corp_data, date):
        for balanceEntry in corp_data:
            if balanceEntry.date == date:
                return "true"
        return None

    def main(self):
        print("## Build BalanceJournal")
        print("establishing connection ...")

        client = MongoProvider().provide()

        transaction_journal = client.transactionjournal
        posday_journal = client.pos_day_journal

        print("loading journal entries ...")
        transactions = []
        for entry in transaction_journal.find():
            transactions.append(entry)
        posdays = []
        for entry in posday_journal.find():
            posdays.append(entry)
        print ("loaded %d transactions and %d posdays" % (len(transactions), len(posdays)))

        print("preparing corp datasets ...")
        corps = {}
        for entry in posdays:
            corps[entry['corpId']] = []
        for entry in transactions:
            corps[entry['corpId']] = []
        print("prepared %d corps" % len(corps))

        print("loading posday expenses ...")
        for posday in posdays:
            corp_id = posday['corpId']
            balance_entry = Balance(posday['date'], -1 * posday['amount'] * POS_DAY_FEE)
            corps[corp_id].append(balance_entry)

        print("adding tax payments ...")
        for transaction in transactions:
            date = transaction['date'].split(' ')[0]
            corp_id = transaction['corpId']
            if self.has_entry_for_date(corps[corp_id], date):
                for balanceEntry in corps[corp_id]:
                    if balanceEntry.date == date:
                        balanceEntry.amount += transaction['amount']
            else:
                corps[corp_id].append(Balance(date, transaction['amount']))

        print("sorting by date ...")
        for corp_id in corps:
            corps[corp_id].sort(key=lambda x: x.date)

        print("summing up balance entries ...")
        for corp_id in corps:
            balance = 0
            for entry in corps[corp_id]:
                balance += entry.amount
                entry.amount = balance

        print("building results ...")
        result = []
        for corp_id in corps:
            # corpId and balance
            corp_data = corps[corp_id]
            last_balance = corp_data[-1].amount
            corp_name = self.get_corp_name(corp_id, client)
            negative_days = self.get_negative_days(corp_data)
            result_entry = {'corpId': corp_id, 'balance': last_balance,
                            'negativeSinceDays': negative_days,
                            'corpName': corp_name}
            result.append(result_entry)

        print("writing results ...")
        client.balance_journal.delete_many({})
        bulk = client.balance_journal.initialize_unordered_bulk_op()
        for element in result:
            bulk.insert(element)

        try:
            bulk.execute()
        except BulkWriteError as bwe:
            pprint(bwe.details)

if __name__ == "__main__":
    BalanceJournalBuilder().main()

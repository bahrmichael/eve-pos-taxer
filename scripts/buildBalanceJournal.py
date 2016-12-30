from pprint import pprint

from pymongo.errors import BulkWriteError

from classes.mongoProvider import MongoProvider

POS_DAY_FEE = 2000000


class Balance:
    def __init__(self, date, amount):
        self.date = date
        self.amount = amount

    def __repr__(self):
        return repr((self.date, self.amount))


def get_negative_days(balance_array):
    reversed_balances = sorted(balance_array, key=lambda x: x.date, reverse=True)
    negative_count = 0
    print len(reversed_balances)
    for balance in reversed_balances:
        print balance
        if balance.amount < 0:
            negative_count += 1
    return negative_count


def get_corp_name(corp_id, mongo_client):
    return mongo_client.corporations.find_one({'corpId': str(corp_id)})['corpName']


def main():
    print "## Build BalanceJournal"
    print "establishing connection ..."

    client = MongoProvider().provide()

    transaction_journal = client.transactionjournal
    posday_journal = client.pos_day_journal

    print "loading journal entries ..."
    transactions = []
    for entry in transaction_journal.find():
        transactions.append(entry)
    posdays = []
    for entry in posday_journal.find():
        posdays.append(entry)

    print "preparing corp datasets ..."
    corps = {}
    for entry in posdays:
        corps[entry['corpId']] = []

    print "loading posday expenses ..."
    for posday in posdays:
        corp_id = posday['corpId']
        balance_entry = Balance(posday['date'], -1 * posday['amount'] * POS_DAY_FEE)
        corps[corp_id].append(balance_entry)

    print "adding tax payments ..."
    for transaction in transactions:
        date = transaction['date'].split(' ')[0]
        corp_id = str(transaction['corpId'])
        for balanceEntry in corps[corp_id]:
            if balanceEntry.date == date:
                balanceEntry.amount += transaction['amount']

    print "sorting by date ..."
    for corp_id in corps:
        corps[corp_id].sort(key=lambda x: x.date)

    print "summing up balance entries ..."
    for corp_id in corps:
        balance = 0
        for entry in corps[corp_id]:
            balance += entry.amount
            entry.amount = balance

    print "building results ..."
    result = []
    for corp_id in corps:
        # corpId and balance
        last_balance = corps[corp_id][-1].amount
        result_entry = {'corpId': corp_id, 'balance': last_balance,
                        'negativeSinceDays': get_negative_days(corps[corp_id]),
                        'corpName': get_corp_name(corp_id, client)}
        result.append(result_entry)

    print "writing results ..."
    client.balance_journal.delete_many({})
    bulk = client.balance_journal.initialize_unordered_bulk_op()
    for element in result:
        bulk.insert(element)

    try:
        bulk.execute()
    except BulkWriteError as bwe:
        pprint(bwe.details)


if __name__ == "__main__":
    main()
from pprint import pprint

from pymongo.errors import BulkWriteError

from classes.mongoProvider import MongoProvider


def main():
    print("## Build DepositJournal")
    print("establishing connection ...")

    client = MongoProvider().provide()

    transaction_journal = client.transactionjournal

    print("loading journal entries ...")
    journals = []
    for entry in transaction_journal.find():
        journals.append(entry)

    print("aggregation journal entries ...")
    aggregate = aggregate_journal(journals)

    print("writing aggregation entries ...")
    client.deposit_journal.delete_many({})
    bulk = client.deposit_journal.initialize_unordered_bulk_op()
    for element in aggregate:
        bulk.insert(element)

    try:
        bulk.execute()
    except BulkWriteError as bwe:
        pprint(bwe.details)


def aggregate_journal(entries):
    aggregated = []
    for entry in entries:
        date_ = entry['date'].split(' ')[0]
        corp_id_ = entry['corpId']
        existing_item = find_existing(date_, aggregated, corp_id_)
        if existing_item is None:
            item = {'date': date_, 'corpId': corp_id_, 'amount': entry['amount']}
            aggregated.append(item)
        else:
            aggregated.remove(existing_item)
            item = {'date': date_, 'corpId': corp_id_,
                    'amount': entry['amount'] + existing_item['amount']}
            aggregated.append(item)

    return aggregated


def find_existing(date, entries, corp_id):
    for entry in entries:
        if entry['date'] == date and entry['corpId'] == corp_id:
            return entry

    return None


if __name__ == "__main__":
    main()

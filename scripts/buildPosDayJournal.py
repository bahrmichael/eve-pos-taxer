from pprint import pprint

from pymongo.errors import BulkWriteError

from classes.mongoProvider import MongoProvider


def is_whitelisted(location_id, client):
    location = client.location_whitelist.find_one({"systemId": long(location_id)})
    return location is not None


def main():
    print "## Build PosDayJournal"
    print "establishing connection ..."

    client = MongoProvider().provide()

    pos_journal = client.posjournal

    print "loading journal entries ..."
    journals = []
    for entry in pos_journal.find():
        if is_whitelisted(entry['locationId'], client):
            journals.append(entry)

    print "aggregation journal entries ..."
    aggregate = aggregate_journal(journals)

    print "writing aggregation entries ..."
    client.pos_day_journal.delete_many({})
    if len(aggregate) > 0:
        bulk = client.pos_day_journal.initialize_unordered_bulk_op()
        for element in aggregate:
            bulk.insert(element)

        try:
            bulk.execute()
        except BulkWriteError as bwe:
            pprint(bwe.details)
    else:
        print "No aggregates were produced"


def aggregate_journal(entries):
    aggregated = []
    for entry in entries:
        date_ = entry['date'].split(' ')[0]
        corp_id_ = entry['corpId']
        existing_item = find_existing(date_, aggregated, corp_id_)
        if existing_item is None:
            item = {'date': date_, 'corpId': corp_id_, 'amount': 1}
            aggregated.append(item)
        else:
            aggregated.remove(existing_item)
            item = {'date': date_, 'corpId': corp_id_,
                    'amount': existing_item['amount'] + 1}
            aggregated.append(item)

    return aggregated


def find_existing(date, entries, corp_id):
    for entry in entries:
        if entry['date'] == date and entry['corpId'] == corp_id:
            return entry

    return None


if __name__ == "__main__":
    main()

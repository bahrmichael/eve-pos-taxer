from pprint import pprint

from eveapimongo import MongoProvider
from pymongo.errors import BulkWriteError


print('Loading function')


def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message']
    print("SNS Message: " + message)
    if message == "pos-parsing-done":
        PosDayJournalBuilder().main()
        return "done"


class PosDayJournalBuilder:

    def main(self):
        print("## Build PosDayJournal")

        print("loading journal entries ...")
        journals = self.find_whitelisted_entries()
        print("loaded %d journal entries" % len(journals))

        print("aggregation journal entries ...")
        aggregate = self.aggregate_journal(journals)
        print("produced %d aggregate entries" % len(aggregate))

        if len(aggregate) > 0:
            print("writing aggregation entries ...")
            MongoProvider().delete_all('pos_day_journal')
            self.write_entries(aggregate)

    def write_entries(self, aggregate):
        bulk = MongoProvider().start_bulk('pos_day_journal')
        for element in aggregate:
            bulk.insert(element)
        try:
            bulk.execute()
        except BulkWriteError as bwe:
            pprint(bwe.details)

    def find_whitelisted_entries(self):
        journals = []
        for entry in MongoProvider().find('posjournal'):
            if self.is_whitelisted(entry['locationId']):
                journals.append(entry)
        return journals

    def is_whitelisted(self, location_id):
        location = MongoProvider().find_one('location_whitelist', {"systemId": int(location_id)})
        return location is not None

    def aggregate_journal(self, entries):
        aggregated = []
        for entry in entries:
            item = self.process_entry(aggregated, entry)
            aggregated.append(item)

        return aggregated

    def process_entry(self, aggregated, entry):
        date_ = entry['date'].split(' ')[0]
        corp_id_ = entry['corpId']

        existing_item = self.find_in_list(date_, corp_id_, aggregated)

        if existing_item is None:
            amount = 1
        else:
            amount = existing_item['amount'] + 1

        return {'date': date_, 'corpId': corp_id_, 'amount': amount}

    def find_in_list(self, date, corp_id, entries):
        for entry in entries:
            if entry['date'] == date and entry['corpId'] == corp_id:
                return entry
        return None

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
        whitelisted_locations = self.find_whitelisted_locations()
        for entry in MongoProvider().find('posjournal'):
            if entry['locationId'] in whitelisted_locations:
                journals.append(entry)
        return journals

    def find_whitelisted_locations(self):
        result = []
        for entry in MongoProvider().find('location_whitelist'):
            result.append(entry['systemId'])
        return result

    def aggregate_journal(self, entries):
        aggregated = {}
        keys = [item['corpId'] for item in entries]
        for key in keys:
            aggregated[key] = {}

        for entry in entries:
            corp_id_ = entry['corpId']
            date_ = entry['date']
            if aggregated[corp_id_] == {}:
                aggregated[corp_id_][date_] = 1
            else:
                try:
                    aggregated[corp_id_][date_] += 1
                except KeyError:
                    aggregated[corp_id_][date_] = 1

        result = []
        for corp in aggregated:
            for date in aggregated[corp]:
                result.append({'date': date, 'corpId': corp, 'amount': aggregated[corp][date]})

        return result

    def find_in_list(self, date, corp_id, entries):
        for entry in entries:
            if entry['date'] == date and entry['corpId'] == corp_id:
                return entry
        return None

if __name__ == "__main__":
    PosDayJournalBuilder().main()

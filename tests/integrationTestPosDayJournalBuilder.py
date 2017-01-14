import unittest
from datetime import datetime

from eveapimongo import MongoProvider


class PosParserIntegrationTest(unittest.TestCase):
    # before running this test, run the posParser and the posDayJournalBuilder script
    def __test_suite(self):
        self.no_duplicates_per_corp()
        self.not_more_aggregates_than_corps()
        self.aggregates_must_match_with_pos_journal()

    def no_duplicates_per_corp(self):
        poses = []
        for journal_entry in MongoProvider().find('pos_day_journal'):
            if journal_entry['date'] == datetime.today().strftime('%Y-%m-%d'):
                corp_id_ = journal_entry['corpId']
                self.assertTrue(corp_id_ not in poses, "duplicate corp " + str(corp_id_))
                poses.append(corp_id_)

    def not_more_aggregates_than_corps(self):
        corp_count = MongoProvider().cursor('corporations').count()
        date = datetime.today().strftime('%Y-%m-%d')
        journal_count = MongoProvider().cursor('pos_day_journal').count({'date': date})
        self.assertTrue(journal_count <= corp_count)

    def aggregates_must_match_with_pos_journal(self):
        whitelist = []
        for entry in MongoProvider().find('location_whitelist'):
            whitelist.append(entry['systemId'])

        date = datetime.today().strftime('%Y-%m-%d')
        all_aggregates = MongoProvider().find_filtered('pos_day_journal', {'date': date})
        for aggregate in all_aggregates:
            count = MongoProvider().cursor('posjournal').count({'corpId': aggregate['corpId'], 'date': date,
                                                                'locationId': {'$in': whitelist}})
            self.assertEqual(count, aggregate['amount'],
                             "corpId %d has an aggregated amount of %d while %d posdays were found"
                             % (aggregate['corpId'], aggregate['amount'], count))

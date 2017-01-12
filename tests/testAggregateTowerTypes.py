import unittest
from datetime import datetime
from unittest import mock

from classes.mongoProvider import MongoProvider
from scripts.aggregateTowerTypes import TowerTypeAggregator


class TestPosDayJournalBuilder(unittest.TestCase):
    def setUp(self):
        self.sut = TowerTypeAggregator()

    def test_main(self):
        # 1. get today's date
        date = "2016-10-10"
        date_method = mock.patch.object(self.sut, 'date_today', return_value=date).start()
        # 2. load today's pos journal with the date from 1
        test_entries = [{'typeId': 1}, {'typeId': 1}, {'typeId': 2}]
        journal_method = mock.patch.object(MongoProvider, 'find_filtered', return_value=test_entries).start()
        # 3. aggregate the poses by typeId
        aggregate_method = mock.patch.object(self.sut, 'aggregate_towers', return_value="aggregate").start()

        # run
        self.sut.main()

        # verify
        self.assertEqual(date_method.call_count, 1)
        self.assertEqual(journal_method.call_count, 1)
        journal_method.assert_called_with('posjournal', {'date': date})
        self.assertEqual(aggregate_method.call_count, 1)
        aggregate_method.assert_called_with(test_entries)

    def test_date_today(self):
        expected = datetime.today().strftime('%Y-%m-%d')

        result = self.sut.date_today()

        self.assertEqual(result, expected)

    def test_aggregate_towers(self):
        test_entries = [{'typeId': 1}, {'typeId': 1}, {'typeId': 2}]
        expected = [{'typeId': 1, 'quantity': 2}, {'typeId': 2, 'quantity': 1}]

        result = self.sut.aggregate_towers(towers=test_entries)

        self.assertEqual(expected, result)

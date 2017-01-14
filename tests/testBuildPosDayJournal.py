import unittest
from unittest import mock
from unittest.mock import MagicMock

from eveapimongo import MongoProvider

from functions.posDayJournalBuilder.posDayJournalBuilder import PosDayJournalBuilder


class TestPosDayJournalBuilder(unittest.TestCase):
    def setUp(self):
        self.sut = PosDayJournalBuilder()

    def test_main(self):
        # prepare
        journals_method = mock.patch.object(self.sut, 'find_whitelisted_entries', return_value="journals").start()
        aggregate_method = mock.patch.object(self.sut, 'aggregate_journal', return_value="aggregate").start()
        delete_method = mock.patch.object(MongoProvider, 'delete_all').start()
        write_method = mock.patch.object(self.sut, 'write_entries').start()

        # run
        self.sut.main()

        # verify
        self.assertEqual(journals_method.call_count, 1)
        self.assertEqual(aggregate_method.call_count, 1)
        aggregate_method.assert_called_with("journals")
        self.assertEqual(delete_method.call_count, 1)
        self.assertEqual(write_method.call_count, 1)
        write_method.assert_called_with("aggregate")

    def test_main_no_aggregates(self):
        # prepare
        journals_method = mock.patch.object(self.sut, 'find_whitelisted_entries', return_value="journals").start()
        aggregate_method = mock.patch.object(self.sut, 'aggregate_journal', return_value="").start()
        delete_method = mock.patch.object(MongoProvider, 'delete_all').start()
        write_method = mock.patch.object(self.sut, 'write_entries').start()

        # run
        self.sut.main()

        # verify
        self.assertEqual(journals_method.call_count, 1)
        self.assertEqual(aggregate_method.call_count, 1)
        aggregate_method.assert_called_with("journals")
        self.assertEqual(delete_method.call_count, 0)
        self.assertEqual(write_method.call_count, 0)

    def test_find_whitelisted_entries(self):
        # prepare
        double_used_entries = [{'locationId': 1, 'systemId': 1}, {'locationId': 2, 'systemId': 2}]
        find_method = mock.patch.object(MongoProvider, 'find', return_value=double_used_entries).start()

        # run
        result = self.sut.find_whitelisted_entries()

        # verify
        self.assertEqual(find_method.call_count, 2)
        self.assertEqual(result, double_used_entries)

    def test_aggregate_journal_multiple_entries_from_one_corp_and_same_day_should_return_one_aggregate(self):
        data = [{'corpId': 123, 'date': 'today'}, {'corpId': 123, 'date': 'today'}, {'corpId': 123, 'date': 'today'}]
        expected = [{'date': 'today', 'corpId': 123, 'amount': 3}]

        result = self.sut.aggregate_journal(data)

        self.assertEqual(len(result), 1)
        self.assertEqual(expected, result)

    def test_aggregate_journal_multiple_entries_from_one_corp_and_two_days_should_return_two_aggregates(self):
        data = [{'corpId': 123, 'date': 'today'}, {'corpId': 123, 'date': 'today'}, {'corpId': 123, 'date': 'otherDay'}]

        result = self.sut.aggregate_journal(data)

        self.assertEqual(len(result), 2)
        for element in result:
            if element['corpId'] == 123 and element['date'] == 'today':
                self.assertEqual(element['amount'], 2)
            else:
                self.assertEqual(element['amount'], 1)

    def test_aggregate_journal_multiple_entries_from_multiple_corp_and_one_day_should_return_two_aggregates(self):
        data = [{'corpId': 1, 'date': 'today'}, {'corpId': 1, 'date': 'today'}, {'corpId': 2, 'date': 'today'}]
        expected = [{'date': 'today', 'corpId': 1, 'amount': 2}, {'date': 'today', 'corpId': 2, 'amount': 1}]

        result = self.sut.aggregate_journal(data)

        self.assertEqual(len(result), 2)
        self.assertEqual(expected, result)

    def test_find_in_list_positive(self):
        entries = [{'date': 'date', 'corpId': 123456}]

        result = self.sut.find_in_list('date', 123456, entries)

        self.assertIsNotNone(result)

    def test_find_in_list_negative(self):
        entries = [{'date': 'date', 'corpId': 123456}]

        result = self.sut.find_in_list('date', -1, entries)

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

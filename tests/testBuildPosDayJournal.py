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
        entries = [{'locationId': 1}, {'locationId': 2}]
        find_journal_method = mock.patch.object(MongoProvider, 'find', return_value=entries).start()
        find_whitelist_method = mock.patch.object(MongoProvider, 'find_one', return_value="something").start()

        # run
        result = self.sut.find_whitelisted_entries()

        # verify
        self.assertEqual(result, entries)
        self.assertEqual(find_journal_method.call_count, 1)
        find_journal_method.assert_called_with('posjournal')
        self.assertEqual(find_whitelist_method.call_count, 2)

    def test_aggregate_journal(self):
        # prepare
        self.sut.process_entry = MagicMock(return_value="entry")

        # run
        result = self.sut.aggregate_journal(['a', 'b'])

        # verify
        self.assertEqual(result, ['entry', 'entry'])

    def test_process_entry_already_in_list(self):
        # prepare
        self.sut.find_in_list = MagicMock(return_value={'amount': 10})
        entry = {'date': 'date time', 'corpId': 0}

        # run
        result = self.sut.process_entry("aggregated", entry)

        # verify
        expected = {'date': 'date', 'corpId': 0, 'amount': 11}
        self.assertEqual(result, expected)

    def test_process_entry_not_in_list(self):
        # prepare
        self.sut.find_in_list = MagicMock(return_value=None)
        entry = {'date': 'date time', 'corpId': 0}

        # run
        result = self.sut.process_entry("aggregated", entry)

        # verify
        expected = {'date': 'date', 'corpId': 0, 'amount': 1}
        self.assertEqual(result, expected)

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

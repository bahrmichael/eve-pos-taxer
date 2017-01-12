import unittest
from datetime import datetime
from unittest import mock

from eveapimongo import ApiWrapper, MongoProvider
from functions.transactionParser.transactionParser import TransactionParser


class TestTransactionParser(unittest.TestCase):
    def setUp(self):
        self.sut = TransactionParser()

    def test_handle_error(self):
        date = datetime.now()
        expected_post = {
            'timestamp': date,
            'message': 'Could not access the WalletJournal API',
            'script': 'loadTransactions',
            'corpId': 123456
        }
        mock.patch.object(self.sut, 'date_now', return_value=date).start()
        insert_method = mock.patch.object(MongoProvider, 'insert').start()

        self.sut.handle_error(123456)

        self.assertEqual(insert_method.call_count, 1)
        insert_method.assert_called_with('error_log', expected_post)

    def test_is_target_recipient(self):
        expected = "recipient"
        row = self.MockRow(expected)
        mock.patch.object(self.sut, 'get_tax_recipient', return_value=expected).start()

        result = self.sut.is_target_recipient(row)

        self.assertTrue(result)

    def test_build_entry(self):
        row = self.MockRow("123")
        expected = {
            "transactionId": 123,
            "date": "123",
            "corpId": 123456,
            "amount": -123
        }

        result = self.sut.build_entry(123456, row)

        self.assertEqual(result, expected)

    def test_process_transaction_not_target_recipient(self):
        target_method = mock.patch.object(self.sut, 'is_target_recipient', return_value=None).start()
        build_method = mock.patch.object(self.sut, 'build_entry', return_value=None).start()

        self.sut.is_target_recipient("test")

        self.assertEqual(target_method.call_count, 1)
        self.assertEqual(build_method.call_count, 0)

    def test_process_transaction_with_new_transaction(self):
        # prepare
        target_method = mock.patch.object(self.sut, 'is_target_recipient', return_value=1).start()
        find_method = mock.patch.object(MongoProvider, 'find_one', return_value=None).start()
        insert_method = mock.patch.object(MongoProvider, 'insert').start()

        row = self.MockRow("123")
        corp_id = 123456

        # run
        self.sut.process_transaction(corp_id, row)

        # verify
        self.assertEqual(target_method.call_count, 1)
        target_method.assert_called_with(row)

        self.assertEqual(find_method.call_count, 1)
        find_method.assert_called_with('transactionjournal', {"transactionId": 123})

        self.assertEqual(insert_method.call_count, 1)

    def test_process_transaction_with_existing_transaction(self):
        # prepare
        target_method = mock.patch.object(self.sut, 'is_target_recipient', return_value=1).start()
        find_method = mock.patch.object(MongoProvider, 'find_one', return_value="found").start()
        insert_method = mock.patch.object(MongoProvider, 'insert').start()

        row = self.MockRow("123")
        corp_id = 123456

        # run
        self.sut.process_transaction(corp_id, row)

        # verify
        self.assertEqual(target_method.call_count, 1)
        target_method.assert_called_with(row)

        self.assertEqual(find_method.call_count, 1)
        find_method.assert_called_with('transactionjournal', {"transactionId": 123})

        self.assertEqual(insert_method.call_count, 0)

    def test_process_corp_with_no_api_result(self):
        mock.patch.object(ApiWrapper, 'call', return_value=None).start()
        handle_method = mock.patch.object(self.sut, 'handle_error').start()

        self.sut.process_corp(123, 'code', 123456)

        self.assertEqual(handle_method.call_count, 1)
        handle_method.assert_called_with(123456)

    def test_process_corp(self):
        api_result = [["test"]]
        mock.patch.object(ApiWrapper, 'call', return_value=api_result).start()
        process_method = mock.patch.object(self.sut, 'process_transaction').start()

        self.sut.process_corp(123, 'code', 123456)

        self.assertEqual(process_method.call_count, 7)
        process_method.assert_called_with(123456, "test")

    def test_main(self):
        corps = [{'key': 123, 'vCode': 'code', 'corpId': 123456, 'corpName': 'name'}]
        mock.patch.object(MongoProvider, 'find', return_value=corps).start()
        process_method = mock.patch.object(self.sut, 'process_corp').start()

        self.sut.main()

        self.assertEqual(process_method.call_count, 1)
        process_method.assert_called_with(123, 'code', 123456)

    class MockRow:
        text = ""

        def __init__(self, text):
            self.text = text

        def get(self, irrelevant_parameter):
            return self.text


if __name__ == '__main__':
    unittest.main()

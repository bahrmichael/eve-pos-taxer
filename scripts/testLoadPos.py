import unittest
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock

from scripts.loadPos import PosParser


class TestPosParser(unittest.TestCase):

    def setUp(self):
        self.sut = PosParser()
        self.sut.get_mongo_collection_cursor = MagicMock(return_value=None)

    def test_main(self):
        # test data
        corps = [{'key': 1, 'vCode': 'v', 'corpId': 2, 'corpName': 't'}]

        # mocking
        find_patcher = mock.patch.object(self.sut, 'db_find', return_value=corps)
        find_patched = find_patcher.start()
        load_patcher = mock.patch.object(self.sut, 'load_for_corp')
        load_patched = load_patcher.start()

        # run
        self.sut.main()

        # verify
        self.assertEqual(find_patched.call_count, 1)
        find_patched.assert_called_with('corporations')
        corp = corps[0]
        self.assertEqual(load_patched.call_count, 1)
        load_patched.assert_called_with(corp['key'], corp['vCode'], corp['corpId'])

    def test_load_for_corp_api_error(self):
        # mocking
        get_patcher = mock.patch.object(self.sut, 'get_starbase_list', return_value=None)
        get_patched = get_patcher.start()
        handle_patcher = mock.patch.object(self.sut, 'handle_error')
        handle_patched = handle_patcher.start()
        process_patcher = mock.patch.object(self.sut, 'process_pos')
        process_patched = process_patcher.start()

        # run
        self.sut.load_for_corp(key_id=1, v_code='v', corp_id=2)

        # verify
        self.assertEqual(get_patched.call_count, 1)
        get_patched.assert_called_with(1, 'v')
        self.assertEqual(handle_patched.call_count, 1)
        handle_patched.assert_called_with(2)
        self.assertEqual(process_patched.call_count, 0)

    def test_load_for_corp_api(self):
        # test data
        api_result = [["api_data"]]

        # mocking
        get_patcher = mock.patch.object(self.sut, 'get_starbase_list', return_value=api_result)
        get_patched = get_patcher.start()
        handle_patcher = mock.patch.object(self.sut, 'handle_error')
        handle_patched = handle_patcher.start()
        process_patcher = mock.patch.object(self.sut, 'process_pos')
        process_patched = process_patcher.start()

        # run
        self.sut.load_for_corp(key_id=1, v_code='v', corp_id=2)

        # verify
        self.assertEqual(get_patched.call_count, 1)
        get_patched.assert_called_with(1, 'v')
        self.assertEqual(handle_patched.call_count, 0)
        self.assertEqual(process_patched.call_count, 1)
        process_patched.assert_called_with(2, "api_data")

    class MockRow:
        text = ""

        def __init__(self, text):
            self.text = text

        def get(self, irrelevant_parameter):
            return self.text

    def test_process_pos(self):
        # test data
        row = self.MockRow(123456)

        # mocking
        find_patcher = mock.patch.object(self.sut, 'db_find_one', return_value="found")
        find_patched = find_patcher.start()
        insert_patcher = mock.patch.object(self.sut, 'db_insert')
        insert_patched = insert_patcher.start()

        # run
        self.sut.process_pos(1, row)

        # verify
        self.assertEqual(find_patched.call_count, 1)
        find_patched.assert_called_with('pos_journal', {"posId": row.get('any'),
                                                        "date": datetime.today().strftime('%Y-%m-%d')})
        self.assertEqual(insert_patched.call_count, 1)

    def test_handle_error(self):
        # test data
        date = datetime.now()
        expected = {
            'timestamp': date,
            'message': 'Could not access the StarbaseList API',
            'script': 'loadPos',
            'corpId': 123456
        }

        # mocking
        insert_patcher = mock.patch.object(self.sut, 'db_insert')
        insert_patched = insert_patcher.start()
        date_patcher= mock.patch.object(self.sut, 'date_now', return_value=date)
        date_patched=date_patcher.start()

        # run
        self.sut.handle_error(expected['corpId'])

        # verify
        self.assertEqual(insert_patched.call_count, 1)
        insert_patched.assert_called_with('error_log', expected)
        self.assertEqual(date_patched.call_count, 1)

if __name__ == '__main__':
    unittest.main()

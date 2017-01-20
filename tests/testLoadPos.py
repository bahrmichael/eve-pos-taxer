import unittest
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock

from eveapimongo import ApiWrapper
from eveapimongo import MongoProvider

from functions.posParser.posParser import PosParser


class TestPosParser(unittest.TestCase):
    def setUp(self):
        self.sut = PosParser()
        self.sut.get_mongo_collection_cursor = MagicMock(return_value=None)

    def test_main(self):
        # test data
        corps = [{'key': 1, 'vCode': 'v', 'corpId': 2, 'corpName': 't'}]
        empty_list = []

        # mocking
        find_poses_patched = mock.patch.object(self.sut, 'find_todays_poses', return_value=empty_list).start()
        find_corps_patched = mock.patch.object(self.sut, 'find_corporations', return_value=corps).start()
        load_patched = mock.patch.object(self.sut, 'load_for_corp', return_value=[1]).start()
        write_method = mock.patch.object(self.sut, 'write_poses').start()
        notify_method = mock.patch.object(self.sut, 'notify_aws_sns').start()

        # run
        self.sut.main()

        # verify
        self.assertEqual(find_poses_patched.call_count, 1)
        self.assertEqual(find_corps_patched.call_count, 1)
        corp = corps[0]
        self.assertEqual(load_patched.call_count, 1)
        load_patched.assert_called_with(corp, empty_list)
        self.assertEqual(write_method.call_count, 1)
        self.assertEqual(notify_method.call_count, 1)

    def test_main_no_new_poses(self):
        # test data
        corps = [{'key': 1, 'vCode': 'v', 'corpId': 2, 'corpName': 't'}]
        empty_list = []

        # mocking
        find_poses_patched = mock.patch.object(self.sut, 'find_todays_poses', return_value=empty_list).start()
        find_corps_patched = mock.patch.object(self.sut, 'find_corporations', return_value=corps).start()
        load_patched = mock.patch.object(self.sut, 'load_for_corp', return_value=empty_list).start()
        write_method = mock.patch.object(self.sut, 'write_poses').start()
        notify_method = mock.patch.object(self.sut, 'notify_aws_sns').start()

        # run
        self.sut.main()

        # verify
        self.assertEqual(find_poses_patched.call_count, 1)
        self.assertEqual(find_corps_patched.call_count, 1)
        corp = corps[0]
        self.assertEqual(load_patched.call_count, 1)
        load_patched.assert_called_with(corp, empty_list)
        self.assertEqual(write_method.call_count, 0)
        self.assertEqual(notify_method.call_count, 0)

    def test_load_for_corp_api_error(self):
        # mocking
        get_patcher = mock.patch.object(ApiWrapper, 'call', return_value=None)
        api_patched = get_patcher.start()
        handle_patcher = mock.patch.object(self.sut, 'handle_error')
        handle_patched = handle_patcher.start()
        process_patcher = mock.patch.object(self.sut, 'process_pos')
        process_patched = process_patcher.start()

        # run
        corp = {'key': 1, 'vCode': 'v', 'corpId': 2}
        self.sut.load_for_corp(corp, existing_poses=[])

        # verify
        self.assertEqual(api_patched.call_count, 1)
        api_patched.assert_called_with(None)
        self.assertEqual(handle_patched.call_count, 1)
        handle_patched.assert_called_with(2)
        self.assertEqual(process_patched.call_count, 0)

    def test_load_for_corp_api(self):
        # test data
        api_result = [["api_data"]]
        empty_pos_list = []

        # mocking
        get_patcher = mock.patch.object(ApiWrapper, 'call', return_value=api_result)
        api_patched = get_patcher.start()
        handle_patcher = mock.patch.object(self.sut, 'handle_error')
        handle_patched = handle_patcher.start()
        process_patcher = mock.patch.object(self.sut, 'process_pos')
        process_patched = process_patcher.start()
        reset_method = mock.patch.object(self.sut, 'reset_fail_count').start()

        # run
        corp = {'key': 1, 'vCode': 'v', 'corpId': 2}
        self.sut.load_for_corp(corp, existing_poses=empty_pos_list)

        # verify
        self.assertEqual(api_patched.call_count, 1)
        api_patched.assert_called_with(None)
        self.assertEqual(handle_patched.call_count, 0)
        self.assertEqual(process_patched.call_count, 1)
        process_patched.assert_called_with(2, "api_data", empty_pos_list)
        self.assertEqual(reset_method.call_count, 1)

    class MockRow:
        text = ""

        def __init__(self, text):
            self.text = text

        def get(self, irrelevant_parameter):
            return self.text

    def test_process_corp_that_failed_more_than_three_times(self):
        corp = {'failCount': 4, 'corpName': 'test'}
        load_patched = mock.patch.object(self.sut, 'load_for_corp').start()

        self.sut.process_corp(corp, None, None)

        self.assertEqual(load_patched.call_count, 0)

    def test_process_corp_that_failed_less_or_equal_three(self):
        corp = {'failCount': 3, 'corpName': 'test', 'key': 1, 'vCode': 'code', 'corpId': 123}
        load_patched = mock.patch.object(self.sut, 'load_for_corp').start()

        self.sut.process_corp(corp, None, None)

        self.assertEqual(load_patched.call_count, 1)

    def test_process_corp_that_didnt_fail(self):
        corp = {'corpName': 'test', 'key': 1, 'vCode': 'code', 'corpId': 123}
        load_patched = mock.patch.object(self.sut, 'load_for_corp').start()

        self.sut.process_corp(corp, None, None)

        self.assertEqual(load_patched.call_count, 1)

    def test_process_pos_exists(self):
        row = self.MockRow('123')
        existing_poses = [{'posId': 123}]

        result = self.sut.process_pos(123456, row, existing_poses)

        self.assertIsNone(result)

    def test_process_pos_is_new(self):
        row = self.MockRow('123')
        existing_poses = [{'posId': 9999999}]

        result = self.sut.process_pos(123456, row, existing_poses)

        self.assertIsNotNone(result)

    def test_handle_error_no_errors_before(self):
        # test data
        expected = {'corpId': 123456, 'corpName': 'Test Corp', 'failCount': 1}

        # mocking
        find_method = mock.patch.object(MongoProvider, 'find_one',
                                        return_value={'corpId': 123456, 'corpName': 'Test Corp'}).start()
        update_method = mock.patch.object(self.sut, 'update_corp').start()
        notify_method = mock.patch.object(self.sut, 'notify_aws_sns').start()

        # run
        self.sut.handle_error(expected['corpId'])

        # verify
        self.assertEqual(find_method.call_count, 1)
        self.assertEqual(update_method.call_count, 1)
        update_method.assert_called_with(expected)
        self.assertEqual(notify_method.call_count, 1)

    def test_handle_error_with_errors_before(self):
        # test data
        expected = {'corpId': 123456, 'corpName': 'Test Corp', 'failCount': 3}

        # mocking
        find_method = mock.patch.object(MongoProvider, 'find_one',
                                        return_value={'corpId': 123456, 'corpName': 'Test Corp', 'failCount': 2}).start()
        update_method = mock.patch.object(self.sut, 'update_corp').start()
        notify_method = mock.patch.object(self.sut, 'notify_aws_sns').start()

        # run
        self.sut.handle_error(expected['corpId'])

        # verify
        self.assertEqual(find_method.call_count, 1)
        self.assertEqual(update_method.call_count, 1)
        update_method.assert_called_with(expected)
        self.assertEqual(notify_method.call_count, 1)

    def test_reset_fail_count_with_failed_corp(self):
        update_method = mock.patch.object(self.sut, 'update_corp').start()
        corp = {'corpId': 123, 'failCount': 3}

        self.sut.reset_fail_count(corp)

        self.assertEqual(update_method.call_count, 1)
        update_method.assert_called_with({'corpId': 123})

    def test_reset_fail_count_with_non_failed_corp(self):
        update_method = mock.patch.object(self.sut, 'update_corp').start()
        corp = {'corpId': 123}

        self.sut.reset_fail_count(corp)

        self.assertEqual(update_method.call_count, 0)


if __name__ == '__main__':
    unittest.main()

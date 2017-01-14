import unittest
from datetime import datetime

from eveapimongo import MongoProvider


class PosParserIntegrationTest(unittest.TestCase):

    # before running this test, run the posParser script
    def test_no_duplicates_must_exist(self):
        poses = []
        date = datetime.today().strftime('%Y-%m-%d')
        for pos_day in MongoProvider().find_filtered('posjournal', {'date': date}):
            pos_id_ = pos_day['posId']
            self.assertTrue(pos_id_ not in poses)
            poses.append(pos_id_)

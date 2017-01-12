import os
from datetime import datetime

from eveapimongo import ApiWrapper
from eveapimongo import MongoProvider

print('Loading function')


def lambda_handler(event, context):
    PosParser().main()
    return "done"


class PosParser:

    endpoint = "/corp/StarbaseList.xml.aspx"

    def main(self):
        print("## Load Poses")
        print("loading corporations ...")

        for corp in MongoProvider().find('corporations'):
            print("loading poses for corp " + corp['corpName'])
            self.load_for_corp(corp['key'], corp['vCode'], corp['corpId'])

        self.notify_aws_sns()

    def notify_aws_sns(self):
        import boto3
        boto3.client('sns').publish(
            TargetArn=os.environ['EVE_POS_SNS_QUEUE'],
            Message='pos-parsing-done'
        )

    def load_for_corp(self, key_id, v_code, corp_id):
        api_result = self.get_starbase_list(key_id, v_code)
        if api_result is None:
            self.handle_error(corp_id)
            return

        for row in api_result[0]:
            self.process_pos(corp_id, row)

    def process_pos(self, corp_id, row):
        post = self.build_entry(corp_id, row)
        found = MongoProvider().find_one('posjournal', {"posId": post['posId'], "date": post['date']})
        if found is not None:
            MongoProvider().insert('posjournal', post)
            print(post['posId'])

    def build_entry(self, corp_id, row):
        post = {
            "posId": int(row.get('itemID')),
            "typeId": int(row.get('typeID')),
            "corpId": corp_id,
            "state": int(row.get('state')),
            "locationId": int(row.get('locationID')),
            "moonId": int(row.get('moonID')),
            "date": datetime.today().strftime('%Y-%m-%d')
        }
        return post

    def handle_error(self, corp_id):
        print("Could not access the pos api for corpId " + str(corp_id))
        post = {
            'timestamp': self.date_now(),
            'message': 'Could not access the StarbaseList API',
            'script': 'loadPos',
            'corpId': corp_id
        }
        MongoProvider().insert('error_log', post)

    def date_now(self):
        return datetime.now()

    def get_starbase_list(self, key_id, v_code):
        return ApiWrapper(self.endpoint, key_id, v_code).call(None)


if __name__ == "__main__":
    PosParser().main()

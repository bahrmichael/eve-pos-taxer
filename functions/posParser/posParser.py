import os
from datetime import datetime

import itertools
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

        print("loading poses that were parsed today ...")
        existing_poses = self.find_todays_poses()
        new_poses = []

        print("loading corporations ...")
        for corp in self.find_corporations():
            self.process_corp(corp, existing_poses, new_poses)

        merged = list(itertools.chain.from_iterable(new_poses))
        if len(merged) > 0:
            print("Writing %d poses" % len(merged))
            self.write_poses(merged)
            self.notify_aws_sns('EVE_POS_SNS_QUEUE', 'pos-parsing-done')
        else:
            print("No new poses to write")

    def reset_fail_count(self, corp):
        if 'failCount' in corp:
            del corp['failCount']
            self.update_corp(corp)

    def find_corporations(self):
        return MongoProvider().find('corporations')

    def write_poses(self, merged):
        MongoProvider().cursor('posjournal').insert_many(merged)

    def find_todays_poses(self):
        result = []
        for entry in MongoProvider().find_filtered('posjournal', {'date': datetime.today().strftime('%Y-%m-%d')}):
            result.append(entry)
        return result

    def process_corp(self, corp, existing_poses, new_poses):
        if 'failCount' not in corp or corp['failCount'] <= 3:
            print("loading poses for corp " + corp['corpName'])
            corp_poses = self.load_for_corp(corp, existing_poses)
            if len(corp_poses) > 0:
                new_poses.append(corp_poses)
        else:
            print("The corp %s has previously failed more than 3 times and will not be parsed." % corp['corpName'])

    def load_for_corp(self, corp, existing_poses):
        poses = []
        api_result = self.get_starbase_list(corp['key'], corp['vCode'])
        if api_result is None:
            self.handle_error(corp['corpId'])
            return []
        else:
            self.reset_fail_count(corp)

        for row in api_result[0]:
            pos = self.process_pos(corp['corpId'], row, existing_poses)
            if pos:
                poses.append(pos)
                # this append is important, so the same pos doesnt get added twice
                existing_poses.append(pos)
        return poses

    def process_pos(self, corp_id, row, existing_poses):
        post = self.build_entry(corp_id, row)
        if not self.exists(post, existing_poses):
            print(post['posId'])
            return post

    def exists(self, post, existing_poses):
        for entry in existing_poses:
            needle = post['posId']
            if needle == entry['posId']:
                return 1
        return 0

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

    def notify_aws_sns(self, topic_variable, message):
        import boto3
        boto3.client('sns').publish(
            TargetArn=os.environ[topic_variable],
            Message=message
        )

    def handle_error(self, corp_id):
        print("Could not access the pos api for corpId " + str(corp_id))

        corp = MongoProvider().find_one('corporations', {'corpId': corp_id})
        if 'failCount' in corp:
            corp['failCount'] += 1
            if corp['failCount'] > 3:
                self.notify_aws_sns('EVE_POS_SNS_ERROR', 'Error parsing API for %s' % corp['corpName'])
        else:
            corp['failCount'] = 1
        self.update_corp(corp)



    def update_corp(self, corp):
        MongoProvider().provide().get_collection('corporations').replace_one({'corpId': corp['corpId']}, corp)

    def get_starbase_list(self, key_id, v_code):
        return ApiWrapper(self.endpoint, key_id, v_code).call(None)


if __name__ == "__main__":
    PosParser().main()

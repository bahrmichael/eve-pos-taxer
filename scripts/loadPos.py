from datetime import datetime

from classes.apiWrapper import ApiWrapper
from classes.mongoProvider import MongoProvider

endpoint = "/corp/StarbaseList.xml.aspx"


def main():
    print("## Load Poses")
    print("establishing connection ...")
    client = MongoProvider().provide()

    for corp in client.corporations.find():
        print("loading poses for corp " + corp['corpName'])
        load_for_corp(client, corp['key'], corp['vCode'], corp['corpId'])


def load_for_corp(mongo_client, key_id, v_code, corp_id):
    pos_journal = mongo_client.posjournal

    api_result = ApiWrapper(endpoint, key_id, v_code).call(None)
    if api_result is None:
        print("Could not access the pos api for corpId " + str(corp_id))
        post = {
            'timestamp': datetime.now(),
            'message': 'Could not access the StarbaseList API',
            'script': 'loadPos',
            'corpId': corp_id
        }
        mongo_client.error_log.insert_one(post)
        return

    for row in api_result[0]:
        location_id = row.get('locationID')
        post = {
            "posId": int(row.get('itemID')),
            "typeId": int(row.get('typeID')),
            "corpId": corp_id,
            "state": int(row.get('state')),
            "locationId": int(location_id),
            "moonId": int(row.get('moonID')),
            "date": datetime.today().strftime('%Y-%m-%d')
        }
        found = pos_journal.find_one({"posId": post['posId'], "date": post['date']})
        if found is None:
            pos_journal.insert_one(post)
            print(post['posId'])

if __name__ == "__main__":
    main()

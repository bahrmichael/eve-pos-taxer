import datetime
import xml.etree.ElementTree

import requests

from classes.mongoProvider import MongoProvider

endpoint = "/corp/StarbaseList.xml.aspx"


def main():
    print "## Load Poses"
    print "establishing connection ..."
    client = MongoProvider().provide()

    for corp in client.corporations.find():
        print "loading poses for corp " + corp['corpName']
        load_for_corp(client.posjournal, corp['key'], corp['vCode'], corp['corpId'])


def load_for_corp(pos_journal, key_id, v_code, corp_id):
    verification = "keyID=%d&vCode=%s" % (key_id, v_code)
    url = "https://api.eveonline.com%s?%s" % (endpoint, verification)
    r = requests.get(url)
    data = r.content
    e = xml.etree.ElementTree.fromstring(data)
    try:
        rows = e[1][0]
    except IndexError:
        print "Could not access the pos api for corpId " + str(corp_id)
        return

    for row in rows:
        location_id = row.get('locationID')
        post = {
            "posId": long(row.get('itemID')),
            "typeId": long(row.get('typeID')),
            "corpId": corp_id,
            "state": int(row.get('state')),
            "locationId": long(location_id),
            "moonId": long(row.get('moonID')),
            "date": datetime.datetime.today().strftime('%Y-%m-%d')
        }
        found = pos_journal.find_one({"posId": post['posId'], "date": post['date']})
        if found is None:
            pos_journal.insert_one(post)
            print post['posId']

if __name__ == "__main__":
    main()

import json
import os
from cgi import parse_qs

from classes.mongoProvider import MongoProvider

POSDAY_FEE = 2000000


def is_favicon(environ):
    return environ.get('PATH_INFO', '').lstrip('/') == "favicon.ico"


def find_deposit(deposits, corp_id):
    for entry in deposits:
        if entry['corpId'] == long(corp_id):
            return entry
    return None


def get_deposit_total_today_all():
    client = MongoProvider().provide()

    # aggregate deposits
    deposits = []
    for deposit in client.deposit_journal.find():
        existing_item = find_deposit(deposits, deposit['corpId'])
        if existing_item is None:
            deposits.append({'corpId': deposit['corpId'], 'amount': deposit['amount']})
        else:
            deposits.remove(existing_item)
            deposits.append({'corpId': deposit['corpId'], 'amount': deposit['amount'] + existing_item['amount']})

    for deposit in deposits:
        corp_id = deposit['corpId']
        deposit['corpName'] = client.corporations.find_one({'corpId': str(corp_id)})['corpName']

    return deposits


def get_balance_all():
    client = MongoProvider().provide()

    result = []
    for entry in client.balance_journal.find():
        # remove the database id
        del entry['_id']
        result.append(entry)

    return result


def process_request(environ):
    url_path = environ.get('PATH_INFO', '').lstrip('/')
    print url_path
    if url_path == "deposit/all":
        return get_deposit_total_today_all()
    elif url_path == "balance/all":
        return get_balance_all()
    elif url_path == "balance/negative":
        negative_balances = []
        for balance in get_balance_all():
            if balance['balance'] < 0:
                negative_balances.append(balance)
        return negative_balances
    elif url_path == "corp":
        body = ''  # b'' for consistency on Python 3.0
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            length = 0
        if length != 0:
            body = json.loads(environ['wsgi.input'].read(length))
            post = {
                'key': body['key'],
                'vCode': body['vCode'],
                'corpId': body['corpId'],
                'corpName': body['corpName']
            }
            database = MongoProvider().provide()
            database.corporations.insert_one(post)
        return {'persisted': body}
    return {'status': 'path ' + url_path + ' not found'}


def app(environ, start_response):
    # skip favicon
    if is_favicon(environ):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ""

    parameters = parse_qs(environ.get('QUERY_STRING', ''))

    # authenticate
    if 'authkey' not in parameters:
        start_response('403 ACCESS DENIED', [('Content-Type', 'text/html')])
        return "Access Denied"
    elif parameters['authkey'] != [os.environ['EVE_POS_AUTHKEY']]:
        start_response('403 ACCESS DENIED', [('Content-Type', 'text/html')])
        return "Access Denied"
    # process request
    else:
        start_response('200 OK', [('Content-Type', 'application/json')])
        response_data = process_request(environ)
        return json.dumps(response_data)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    port = 9000
    srv = make_server('0.0.0.0', port, app)

    print "listening on port " + str(port)
    srv.serve_forever()

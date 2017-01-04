import json
import os
from cgi import parse_qs
from datetime import datetime

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
        deposit['corpName'] = client.corporations.find_one({'corpId': corp_id})['corpName']

    return deposits


def get_balance_all():
    client = MongoProvider().provide()

    result = []
    for entry in client.balance_journal.find():
        # remove the database id
        del entry['_id']
        result.append(entry)

    return result


def get_all_errors():
    errors = []
    for error in MongoProvider().provide().error_log.find():
        del error['_id']
        errors.append(error)
    return errors


def delete_errors():
    MongoProvider().provide().error_log.delete_many({})
    # add en empty element so the csv parser doesn't break
    return [{}]


def get_poscount_today_all():
    journal = MongoProvider().provide().pos_day_journal
    corps = MongoProvider().provide().corporations
    date = datetime.today().strftime('%Y-%m-%d')
    result = []
    for entry in journal.find({'date': date}):
        corp = corps.find_one({'corpId': entry['corpId']})
        result.append({'corp': corp['corpName'], 'amount': entry['amount'], 'date': date})
    return result


def get_poscount_today_all_sum():
    total_count = 0
    for poscount in get_poscount_today_all():
        total_count += poscount['amount']
    return [{'totalPosCount': total_count}]


def get_deposit_all_sum():
    total = 0
    for deposit in get_deposit_total_today_all():
        total += deposit['amount']
    return [{'totalDeposit': total}]


def process_request(environ):
    url_path = environ.get('PATH_INFO', '').lstrip('/')
    print url_path
    if url_path == "deposit/all":
        return get_deposit_total_today_all()
    elif url_path == "deposit/all/sum":
        return get_deposit_all_sum()
    elif url_path == "poscount/all":
        return get_poscount_today_all()
    elif url_path == "poscount/all/sum":
        return get_poscount_today_all_sum()
    elif url_path == "balance/all":
        return get_balance_all()
    elif url_path == "balance/negative":
        negative_balances = []
        for balance in get_balance_all():
            if balance['balance'] < 0:
                negative_balances.append(balance)
        return negative_balances
    elif url_path == "errors":
        return get_all_errors()
    elif url_path == "errors/delete":
        return delete_errors()
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
    elif environ.get('PATH_INFO', '').lstrip('/') == "":
        start_response('200 OK', [('Content-Type', 'text/html')])
        authkey = os.environ['EVE_POS_AUTHKEY']
        error_count = len(get_all_errors())
        result = '''
            <a href="deposit/all?authkey=%s&csv=true">deposit/all csv</a>
            <a href="deposit/all/sum?authkey=%s&csv=true">deposit/all/sum csv</a>
            <a href="poscount/all?authkey=%s&csv=true">poscount/all csv</a>
            <a href="poscount/all/sum?authkey=%s&csv=true">poscount/all/sum csv</a>
            <a href="balance/all?authkey=%s&csv=true">balance/all csv</a>
            <a href="balance/negative?authkey=%s&csv=true">balance/negative csv</a>
        ''' % (authkey, authkey, authkey, authkey, authkey, authkey)

        if error_count > 0:
            result += '''
                <br/>
                <a href="errors?authkey=%s&csv=true">errors (%d) csv</a>
                <a href="errors/delete?authkey=%s&csv=true">clear errors</a>
            ''' % (authkey, error_count, authkey)
        else:
            result += '<br/> 0 errors'
        return result

    # process request
    else:
        response_data = process_request(environ)
        if "csv" in parameters and parameters['csv'] == ['true']:
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return to_csv(response_data)
        else:
            start_response('200 OK', [('Content-Type', 'application/json')])
            return json.dumps(response_data)


def to_csv(response_data):
    header_list = []
    for k, v in response_data[0].iteritems():
        header_list.append(str(k))
    header = ";".join(header_list)
    rows = [header]
    for row in response_data:
        row_list = []
        for k, v in row.iteritems():
            row_list.append(str(v))
        rows.append(";".join(row_list))
    return "\n".join(rows)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    port = 9000
    srv = make_server('0.0.0.0', port, app)

    print "listening on port " + str(port)
    srv.serve_forever()

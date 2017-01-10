import requests
import xml.etree.ElementTree


class ApiWrapper:
    def __init__(self, endpoint, key_id, v_code):
        self.endpoint = endpoint
        self.key_id = key_id
        self.v_code = v_code

    def call(self, parameters):
        verification = "keyID=%d&vCode=%s" % (self.key_id, self.v_code)
        url = "https://api.eveonline.com%s?%s" % (self.endpoint, verification)
        if parameters:
            for parameter in parameters:
                url += "&" + str(parameter) + "=" + str(parameters[parameter])
        r = requests.get(url)
        data = r.content
        e = xml.etree.ElementTree.fromstring(data)
        result = e[1]
        if result.tag == 'error':
            print("ERROR: " + result.text)
            return None
        else:
            return result

from pymongo import MongoClient


class MongoFactory:
    def __init__(self, url, port, database, username, password):
        self.username = username
        self.database = database
        self.port = port
        self.url = url
        self.password = password

    def build(self):
        if self.username is None or self.password is None:
            authentication = ""
        else:
            authentication = "%s:%s@" % (self.username, self.password)
        full_url = "%s%s:%s/%s" % (authentication, self.url, self.port, self.database)
        connect_string = 'mongodb://%s' % full_url
        return MongoClient(connect_string)

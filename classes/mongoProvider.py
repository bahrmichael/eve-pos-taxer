import os

from classes.mongoFactory import MongoFactory


class MongoProvider:
    def __init__(self):
        self.database = os.environ['EVE_POS_DB_NAME']
        self.port = os.environ['EVE_POS_DB_PORT']
        self.url = os.environ['EVE_POS_DB_URL']
        try:
            self.username = os.environ['EVE_POS_DB_USERNAME']
            if self.username == "":
                raise KeyError
        except KeyError:
            print("The environment variable EVE_POS_DB_USERNAME was not set.")
            self.username = None
        try:
            self.password = os.environ['EVE_POS_DB_PASSWORD']
            if self.password == "":
                raise KeyError
        except KeyError:
            print("The environment variable EVE_POS_DB_PASSWORD was not set.")
            self.password = None

    def provide(self):
        return MongoFactory(self.url, self.port, self.database, self.username, self.password).build()[self.database]

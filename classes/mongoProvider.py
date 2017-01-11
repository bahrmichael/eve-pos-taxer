import os

from classes.mongoFactory import MongoFactory


class MongoProvider:
    def __init__(self):
        self.database = self.init_property('EVE_POS_DB_NAME')
        self.port = self.init_property('EVE_POS_DB_PORT')
        self.url = self.init_property('EVE_POS_DB_URL')
        self.username = self.init_property('EVE_POS_DB_USERNAME')
        self.password = self.init_property('EVE_POS_DB_PASSWORD')

    def init_property(self, env_var):
        try:
            field = os.environ[env_var]
            if field == "":
                raise KeyError
            return field
        except KeyError:
            print("The environment variable " + env_var + " was not set.")
            return None

    def provide(self):
        return MongoFactory(self.url, self.port, self.database, self.username, self.password).build()[self.database]

    def cursor(self, collection):
        return self.provide()[collection]

    def find(self, collection):
        return self.cursor(collection).find()

    def find_filtered(self, collection, parameters):
        return self.cursor(collection).find(parameters)

    def find_one(self, collection, parameters):
        return self.cursor(collection).find_one(parameters)

    def insert(self, collection, post):
        self.cursor(collection).insert_one(post)

    def delete_all(self, collection):
        self.cursor(collection).delete_many({})

    def start_bulk(self, collection):
        return self.cursor(collection).initialize_unordered_bulk_op()

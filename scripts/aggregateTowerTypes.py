from datetime import datetime
from pprint import pprint

from classes.mongoProvider import MongoProvider


class TowerTypeAggregator:

    def main(self):
        date = self.date_today()
        towers = MongoProvider().find_filtered('posjournal', {'date': date})
        result = self.aggregate_towers(towers)
        pprint(result)

    def date_today(self):
        return datetime.today().strftime('%Y-%m-%d')

    def aggregate_towers(self, towers):
        result = []
        for tower in towers:
            type_id = tower['typeId']
            added = 0
            for entry in result:
                if entry['typeId'] == type_id:
                    entry['quantity'] += 1
                    added = 1
                    break
            if not added:
                result.append({'typeId': type_id, 'quantity': 1})
        return result

if __name__ == "__main__":
    TowerTypeAggregator().main()

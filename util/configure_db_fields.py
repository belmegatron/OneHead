import decimal

from onehead.common import OneHeadCommon
from onehead.db import OneHeadDB
from pprint import pprint

if __name__ == "__main__":

    config = OneHeadCommon.load_config()
    database = OneHeadDB(config)

    scoreboard = database.retrieve_table()
    players = [x["name"] for x in scoreboard]

    for player in players:
        database.db.update_item(
            Key={"name": player},
            UpdateExpression="set rbucks = :zero",
            ExpressionAttributeValues={":zero": decimal.Decimal(0)},
            ReturnValues="UPDATED_NEW",
        )

    scoreboard = database.retrieve_table()
    pprint(scoreboard)
import json
import decimal

import boto3
from botocore.exceptions import ClientError
from discord.ext import commands

from onehead.common import OneHeadException


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


class OneHeadDB(commands.Cog):
    def __init__(self, config):

        dynamo_config_settings = config["aws"]["dynamodb"]
        self.dynamo = boto3.resource(
            "dynamodb", region_name=dynamo_config_settings["region"]
        )
        self.db = self.dynamo.Table(dynamo_config_settings["tables"]["dota"])

    def player_exists(self, player_name):

        try:
            response = self.db.get_item(Key={"name": player_name})
        except ClientError as e:
            print(e)
        else:
            if response.get("Item"):
                return True
            else:
                return False

    def add_player(self, player_name, mmr):

        if not isinstance(player_name, str):
            raise OneHeadException("Player Name not a valid string.")

        if self.player_exists(player_name) is False:
            self.db.put_item(
                Item={"name": player_name, "win": 0, "loss": 0, "mmr": int(mmr)}
            )

    def remove_player(self, player_name):

        if not isinstance(player_name, str):
            raise OneHeadException("Player name not a valid string.")

        if self.player_exists(player_name):
            try:
                self.db.delete_item(Key={"name": player_name})
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    print(e.response["Error"]["Message"])
                else:
                    raise
            else:
                print("{} has been deleted.".format(player_name))

    def update_player(self, player_name, win):

        if not isinstance(win, bool):
            raise OneHeadException("Win parameter must be a valid bool.")

        if not isinstance(player_name, str):
            raise OneHeadException("Player Name not a valid string.")

        if self.player_exists(player_name) is False:
            raise OneHeadException("{} cannot be found.".format(player_name))

        if win:
            self.db.update_item(
                Key={"name": player_name},
                UpdateExpression="set win = win + :val",
                ExpressionAttributeValues={":val": decimal.Decimal(1)},
                ReturnValues="UPDATED_NEW",
            )
        else:
            self.db.update_item(
                Key={"name": player_name},
                UpdateExpression="set loss = loss + :val",
                ExpressionAttributeValues={":val": decimal.Decimal(1)},
                ReturnValues="UPDATED_NEW",
            )

    def lookup_player(self, player_name):

        try:
            response = self.db.get_item(Key={"name": player_name})
        except ClientError as e:
            print(e)
        else:
            item = response.get("Item")
            player = json.dumps(item, indent=4, cls=DecimalEncoder)
            player = json.loads(player)
            return player

    def retrieve_table(self):

        try:
            response = self.db.scan()
        except ClientError as e:
            print(e)
        else:
            table = response.get("Items")
            table = json.dumps(table, indent=4, cls=DecimalEncoder)
            table = json.loads(table)
            return table

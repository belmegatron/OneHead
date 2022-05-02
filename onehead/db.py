import decimal
import json

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
    def __init__(self, config: dict):

        dynamo_config_settings = config["aws"]["dynamodb"]
        self.dynamo = boto3.resource(
            "dynamodb", region_name=dynamo_config_settings["region"]
        )
        self.db = self.dynamo.Table(dynamo_config_settings["tables"]["dota"])

    def player_exists(self, player_name: str) -> bool:

        try:
            response = self.db.get_item(Key={"name": player_name})
        except ClientError as e:
            raise OneHeadException(e)
        else:
            if response.get("Item"):
                return True
            else:
                return False

    def add_player(self, player_name: str, mmr: int):

        if not isinstance(player_name, str):
            raise OneHeadException("Player Name not a valid string.")

        if self.player_exists(player_name) is False:
            self.db.put_item(
                Item={
                    "name": player_name,
                    "win": 0,
                    "loss": 0,
                    "mmr": mmr,
                    "win_streak": 0,
                    "loss_streak": 0,
                    "rbucks": 0
                }
            )

    def remove_player(self, player_name: str):

        if not isinstance(player_name, str):
            raise OneHeadException("Player name not a valid string.")

        if self.player_exists(player_name):
            try:
                self.db.delete_item(Key={"name": player_name})
            except ClientError as e:
                raise OneHeadException(e)

    def update_player(self, player_name: str, win: bool):

        if not isinstance(win, bool):
            raise OneHeadException("Win parameter must be a valid bool.")

        if not isinstance(player_name, str):
            raise OneHeadException("Player Name not a valid string.")

        if self.player_exists(player_name) is False:
            raise OneHeadException(f"{player_name} cannot be found.")

        if win:
            self.db.update_item(
                Key={"name": player_name},
                UpdateExpression="set win = win + :val, win_streak = win_streak + :val, loss_streak = :zero",
                ExpressionAttributeValues={
                    ":val": decimal.Decimal(1),
                    ":zero": decimal.Decimal(0),
                },
                ReturnValues="UPDATED_NEW",
            )
        else:
            self.db.update_item(
                Key={"name": player_name},
                UpdateExpression="set loss = loss + :val, win_streak = :zero, loss_streak = loss_streak + :val",
                ExpressionAttributeValues={
                    ":val": decimal.Decimal(1),
                    ":zero": decimal.Decimal(0),
                },
                ReturnValues="UPDATED_NEW",
            )

    def lookup_player(self, player_name: str) -> dict:

        try:
            response = self.db.get_item(Key={"name": player_name})
        except ClientError as e:
            raise OneHeadException(e)
        else:
            item = response.get("Item")
            player = json.dumps(item, indent=4, cls=DecimalEncoder)
            player = json.loads(player)
            return player

    def retrieve_table(self) -> list[dict]:

        try:
            response = self.db.scan()
        except ClientError as e:
            raise OneHeadException(e)
        else:
            table = response.get("Items")
            table = json.dumps(table, indent=4, cls=DecimalEncoder)
            table = json.loads(table)
            return table

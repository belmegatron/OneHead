import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')

table = dynamodb.Table('onehead')

with open("..\db.json") as f:
    db = json.load(f)
    players = db["_default"]

for key, player in players.items():

    try:
        name = player["name"]
        win = player["win"]
        loss = player["loss"]
        mmr = player["mmr"]
    except:
        continue

    table.put_item(
        Item={
            "name": name,
            "win": win,
            "loss": loss,
            "mmr": mmr
        }
    )

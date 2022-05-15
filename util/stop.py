import json

import boto3

client = boto3.client("ecs")


def find_task():
    response = client.list_tasks(
        cluster="onehead", maxResults=10, desiredStatus="RUNNING", launchType="FARGATE"
    )

    return response


def stop_task(arn):
    response = client.stop_task(cluster="onehead", task=arn, reason="Scheduled Close")

    return response


def lambda_handler(event, context):
    resp = find_task()
    task_arns = resp.get("taskArns")
    if task_arns:
        arn = task_arns[0]
        stop_task(arn)

    return {"statusCode": 200, "body": json.dumps("Stopped")}

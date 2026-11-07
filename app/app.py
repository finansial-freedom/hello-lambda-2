import json
import boto3
import os

secretname = os.environ.get('SECRET_NAME')
client_secretsmanager = boto3.client('secretsmanager')


def handler(event, context):
    print(json.dumps(event))
    response = client.get_secret_value(
        SecretId=secretname
    )
    print(json.loads(response))
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message_lambda": "Hello World from Ivan!",
            "message": "Hardcoded message",
            "owner": "Hardcoded owner",
            "env": "hardcoded",
        }),
    }

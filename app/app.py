import json
import boto3
import os

secretname = os.environ.get('SECRET_NAME')
client_secretsmanager = boto3.client('secretsmanager', region_name='us-west-2')


def handler(event, context):
    print(json.dumps(event))
    response = client_secretsmanager.get_secret_value(
        SecretId=secretname
    )
    print(response)
    secret = json.loads(response['SecretString'])
    message = secret['message']
    owner = secret['owner']
    env = secret['env']
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message_lambda": "Hello World from Ivan!",
            "message": message,
            "owner": owner,
            "env": env,
        }),
    }

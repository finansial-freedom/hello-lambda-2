import json


def handler(event, context):

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message_lambda": "Hello World!",
            "message": "Hardcoded message",
            "owner": "Hardcoded owner",
            "env": "hardcoded",
        }),
    }

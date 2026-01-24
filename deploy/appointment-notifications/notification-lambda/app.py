import json 
import boto3
import os

ses = boto3.client("ses")
SOURCE_EMAIL = os.environ["SOURCE_EMAIL"]

def handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])

        recipient = body["email"]
        subject = body["subject"]
        message = body["message"]

        ses.send_email(
            Source=SOURCE_EMAIL,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": message}
                }
            }
        )
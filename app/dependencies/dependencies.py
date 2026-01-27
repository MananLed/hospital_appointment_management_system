import boto3
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_sns import SNSClient
from app.constants.constants import REGION

ddb_connection: DynamoDBClient = boto3.client("dynamodb", region_name=REGION)
sns_client: SNSClient = boto3.client("sns", region_name=REGION)

import boto3
from app.constants.constants import REGION

ddb_connection = boto3.client("dynamodb", region_name=REGION)
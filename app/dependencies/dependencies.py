import boto3
from app.constants.constants import REGION


cognito_client = boto3.client("cognito-idp", region_name=REGION)
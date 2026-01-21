from app.repository.auth_repository import AuthRepository
from app.dependencies.dependencies import cognito_client
from boto3.dynamodb.types import TypeDeserializer

auth_repository_instance = AuthRepository(cognito_client, "", TypeDeserializer, "")
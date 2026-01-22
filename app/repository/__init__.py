from app.repository.user_repository import UserRepository
from app.dependencies.dependencies import ddb_connection
from boto3.dynamodb.types import TypeDeserializer
from app.constants.constants import TABLE_NAME

user_repository_instance = UserRepository(ddb_connection, TypeDeserializer, TABLE_NAME)
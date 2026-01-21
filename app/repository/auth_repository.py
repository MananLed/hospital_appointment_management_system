from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.dto.user import SignUpInput
from app.constants.constants import CLIENT_ID, USER_POOL_ID

class AuthRepository:
    def __init__(self, cognito_client, ddb_connection, deserializer, table_name):
        self.deserializer = deserializer()
        self.dynamodb = ddb_connection
        self.cognito = cognito_client
        self.table_name = table_name

    def get_access_token(self, email, password):
        try:
            response = self.cognito.initiate_auth(
                ClientId=CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password
                }
            )

            auth_result = response["AuthenticationResult"]
            return {
                "id_token": auth_result.get("IdToken"),
                "access_token": auth_result.get("AccessToken"),
                "refresh_token": auth_result.get("RefreshToken"),
                "expires_in": auth_result.get("ExpiresIn"),
                "token_type": auth_result.get("TokenType")
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ["NotAuthorizedException", "UserNotFoundException"]:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            else:
                raise HTTPException(status_code=400, detail=str(e))
            
            
    def add_user(self, signup_details: SignUpInput):  # Add Role
        try:
            self.cognito.admin_create_user(
                UserPoolId=USER_POOL_ID,
                Username=signup_details.email,
                UserAttributes=[
                    {"Name": "email", "Value": signup_details.email},
                    {"Name": "name", "Value": signup_details.name},
                    {"Name": "phone_number", "Value": signup_details.mobile},
                    {"Name": "custom:role", "Value": "patient"},
                    {"Name": "custom:department", "Value": signup_details.department or ""}
                ],
                MessageAction="SUPPRESS" 
            )

            self.cognito.admin_set_user_password( 
                UserPoolId=USER_POOL_ID, 
                Username=signup_details.email, 
                Password=signup_details.password, 
                Permanent=True 
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Internal Server Error")


        

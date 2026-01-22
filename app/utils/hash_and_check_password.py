from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes = ['bcrypt'])

def generate_hash_from_password(password: str):
    return bcrypt_context.hash(password)

def compare_hash_and_password(input_password: str, hashed_password: str):
    if not bcrypt_context.verify(input_password, hashed_password):
        return False
    return True


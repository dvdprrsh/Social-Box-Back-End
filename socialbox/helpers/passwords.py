import uuid

from passlib.hash import pbkdf2_sha256 as sha256

def hash_password(password):
	return sha256.hash(password)

def verify_password(password, hash):
	return sha256.verify(password, hash)

def generate_api_key():
	return str(uuid.uuid4())

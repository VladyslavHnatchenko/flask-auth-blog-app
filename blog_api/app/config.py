import secrets

SECRET_KEY = secrets.token_hex(16)
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:pg2023@db/blog_db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

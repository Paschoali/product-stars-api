import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    # Auth
    SECRET_KEY = os.getenv('SECRET_KEY')
    PASSWORD = os.getenv('PASSWORD')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

    # External
    EXTERNAL_API = os.getenv('EXTERNAL_API')

    # Pagination
    ITEMS_PER_PAGE = os.getenv('ITEMS_PER_PAGE')

    # Cache
    CACHE_TYPE = os.getenv('CACHE_TYPE')

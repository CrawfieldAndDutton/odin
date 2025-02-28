import mongoengine
from app.config import settings


def connect_to_mongodb():
    mongoengine.connect(host=settings.MONGODB_URI)


def close_mongodb_connection():
    mongoengine.disconnect()

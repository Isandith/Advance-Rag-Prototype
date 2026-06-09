from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI, DB_NAME

client: AsyncIOMotorClient = None
db = None


async def connect():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    print(f"Connected to MongoDB: {DB_NAME}")


async def disconnect():
    global client
    if client:
        client.close()


def get_db():
    return db

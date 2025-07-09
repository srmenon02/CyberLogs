import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_mongo():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["cryptosecure"]
    collection = db["logs"]

    cursor = collection.find().limit(5)
    logs = []
    async for doc in cursor:
        print(doc)
        logs.append(doc)
    client.close()

asyncio.run(test_mongo())

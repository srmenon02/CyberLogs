import asyncio
import json
from fastapi import FastAPI
from kafka import KafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB and Kafka config
MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "cryptosecure"
COLLECTION_NAME = "logs"
KAFKA_TOPIC = "test-logs"
KAFKA_BOOTSTRAP_SERVERS = "localhost:50849"

# Initialize MongoDB client and collection once for reuse
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


from fastapi.responses import JSONResponse
from fastapi import Query

app = FastAPI()

consumer_task = None  # Will hold the asyncio Task for the Kafka consumer


def get_kafka_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='cryptosecure-group',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )


async def save_log(log):
    try:
        result = await collection.insert_one(log)
        print(f"Saved log with id: {result.inserted_id}")
    except Exception as e:
        print(f"Error saving log to MongoDB: {e}")


async def consume_and_store():
    consumer = get_kafka_consumer()
    print("✅ Kafka consumer connected. Listening for messages...")

    try:
        for message in consumer:
            log_data = message.value
            print(f"📥 Received: {log_data}")
            await save_log(log_data)  # <-- await here to ensure save happens
    except Exception as e:
        print(f"Kafka consumer error: {e}")
    finally:
        consumer.close()
        client.close()
        print("Kafka consumer stopped.")



@app.get("/health")
async def health():
    return {"status": "ok"}

# HTTP endpoint to get latest logs
@app.get("/logs")
async def get_logs(limit: int = Query(10, ge=1, le=100)):
    """Return the latest logs from MongoDB, most recent first."""
    cursor = collection.find().sort("_id", -1).limit(limit)
    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)
    return JSONResponse(content=logs)

@app.get("/")
async def root():
    return {"message": "Welcome to CryptoSecure Insights API"}


@app.on_event("startup")
async def startup_event():
    global consumer_task
    # Start Kafka consumer as background task
    consumer_task = asyncio.create_task(consume_and_store())


@app.on_event("shutdown")
async def shutdown_event():
    global consumer_task
    if consumer_task:
        consumer_task.cancel()
        print("Kafka consumer task cancelled.")

import asyncio
import json
from threading import Thread
from kafka import KafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI

MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "cryptosecure"
COLLECTION_NAME = "logs"
KAFKA_TOPIC = "test-logs"
KAFKA_BOOTSTRAP_SERVERS = "localhost:50849"

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

app = FastAPI()

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

def consume_sync(loop):
    consumer = get_kafka_consumer()
    print("✅ Kafka consumer connected. Listening for messages...")

    for message in consumer:
        log_data = message.value
        print(f"📥 Received: {log_data}")
        # Schedule async save_log on the event loop thread-safe way
        asyncio.run_coroutine_threadsafe(save_log(log_data), loop)

@app.on_event("startup")
def startup_event():
    loop = asyncio.get_event_loop()
    thread = Thread(target=consume_sync, args=(loop,), daemon=True)
    thread.start()

@app.on_event("shutdown")
def shutdown_event():
    print("Shutdown: you might want to add cleanup here")

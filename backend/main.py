from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorClient
from kafka import KafkaConsumer
import asyncio
import json

# Configs
MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "cryptosecure"
COLLECTION_NAME = "logs"
KAFKA_TOPIC = "test-logs"
KAFKA_BOOTSTRAP_SERVERS = "localhost:50849"

# MongoDB
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# FastAPI app
app = FastAPI()

# ✅ CORS Middleware must be added before routes or startup events
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/logs")
async def get_logs(limit: int = 10):
    print(f"Fetching latest {limit} logs from MongoDB")
    cursor = collection.find().sort("_id", -1).limit(limit)
    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)
    print(f"Returning {len(logs)} logs")
    return logs


# Kafka consumer background task and control
consumer_task = None

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
    loop = asyncio.get_event_loop()
    try:
        while True:
            # Poll with timeout to allow task cancellation
            msg_pack = consumer.poll(timeout_ms=1000)
            if not msg_pack:
                await asyncio.sleep(0)  # Yield to event loop
                continue
            for tp, messages in msg_pack.items():
                for message in messages:
                    log_data = message.value
                    print(f"📥 Received: {log_data}")
                    loop.create_task(save_log(log_data))
    except asyncio.CancelledError:
        print("Kafka consumer task cancelled via asyncio.")
    except Exception as e:
        print(f"Kafka error: {e}")
    finally:
        consumer.close()
        print("Kafka consumer closed.")

@app.on_event("startup")
async def startup_event():
    global consumer_task
    # Uncomment this line to start Kafka consumer on app startup
    # consumer_task = asyncio.create_task(consume_and_store())

@app.on_event("shutdown")
async def shutdown_event():
    global consumer_task
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        print("Kafka consumer task cancelled gracefully.")

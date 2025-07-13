from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorClient
from kafka import KafkaConsumer
from typing import Optional
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, validator
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

def validate_iso_datetime(value: Optional[str], field_name: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid ISO datetime format for '{field_name}'. "
                   f"Expected format like '2025-07-11T12:00:00'.",
        )
@app.get("/logs")
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    level: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    sort_by: str = Query("timestamp"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    event_keyword: Optional[str] = Query(None, description="Substring to match in event field"),
    host: Optional[str] = Query(None, description="Filter logs by exact host name"),
):
    start_dt = validate_iso_datetime(start_time, "start_time")
    end_dt = validate_iso_datetime(end_time, "end_time")

    query: dict = {}
    if level:
        query["level"] = level
    if host:
        query["host"] = host
    if event_keyword:
        query["event"] = {"$regex": event_keyword, "$options": "i"}
    if start_dt or end_dt:
        time_filter: dict = {}
        if start_dt:
            time_filter["$gte"] = start_dt
        if end_dt:
            time_filter["$lte"] = end_dt
        query["timestamp"] = time_filter

    # Validate sorting
    allowed_sort_fields = {"timestamp", "level", "_id"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Choose from {allowed_sort_fields}")
    sort_direction = 1 if sort_order == "asc" else -1

    total_count = await collection.count_documents(query)
    skip = (page - 1) * page_size
    cursor = collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(page_size)

    logs = []
    async for log in cursor:
        log["_id"] = str(log["_id"])
        logs.append(log)

    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "logs": logs,
    }






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
    consumer_task = asyncio.create_task(consume_and_store())

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

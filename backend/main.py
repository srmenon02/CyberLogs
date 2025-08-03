from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query, HTTPException
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.responses import StreamingResponse
import io
from kafka import KafkaConsumer
from typing import Optional
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, validator
import asyncio
import json
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
import os
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FIXED: Only create FastAPI app once
app = FastAPI(title="CryptoSecure Logs API", version="1.0.0")

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://fly.io/apps/backend-wandering-bird-8180/configuration",  # Add your production frontend URL when you deploy it
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configs
load_dotenv()
MONGODB_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "cryptosecure"
COLLECTION_NAME = "logs"
KAFKA_TOPIC = "test-logs"
KAFKA_BOOTSTRAP_SERVERS = "localhost:50849"

logger.info(f"🔧 Configuration loaded:")
logger.info(f"   DATABASE_NAME: {DATABASE_NAME}")
logger.info(f"   COLLECTION_NAME: {COLLECTION_NAME}")
logger.info(f"   MONGODB_URI exists: {bool(MONGODB_URI)}")
logger.info(f"   KAFKA_TOPIC: {KAFKA_TOPIC}")

# MongoDB client (will be initialized in startup)
client = None
db = None
collection = None

@app.get("/")
async def root():
    logger.info("📥 Root endpoint called")
    return {
        "message": "CryptoSecure Logs API", 
        "status": "running",
        "mongodb_connected": client is not None,
        "endpoints": ["/health", "/logs", "/logs/export"]
    }

@app.get("/health")
async def health():
    logger.info("📥 Health check endpoint called")
    try:
        # Test MongoDB connection
        if client:
            await client.admin.command('ping')
            logger.info("✅ Health check: MongoDB ping successful")
            return {"status": "ok", "mongodb": "connected"}
        logger.warning("⚠️ Health check: MongoDB client not initialized")
        return {"status": "ok", "mongodb": "not_initialized"}
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {"status": "error", "message": str(e)}

def validate_iso_datetime(value: Optional[str], field_name: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        logger.error(f"❌ Invalid datetime format for {field_name}: {value}")
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
    logger.info(f"📥 Get logs called with params: page={page}, page_size={page_size}, level={level}, host={host}")
    
    if collection is None:
        logger.error("❌ Database collection not available")
        raise HTTPException(status_code=503, detail="Database not available")
        
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

    logger.info(f"🔍 MongoDB query: {query}")

    # Validate sorting
    allowed_sort_fields = {"timestamp", "level", "_id"}
    if sort_by not in allowed_sort_fields:
        logger.error(f"❌ Invalid sort field: {sort_by}")
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Choose from {allowed_sort_fields}")
    sort_direction = 1 if sort_order == "asc" else -1

    try:
        total_count = await collection.count_documents(query)
        logger.info(f"📊 Total documents matching query: {total_count}")
        
        skip = (page - 1) * page_size
        projection = {
            "_id": 1,
            "timestamp": 1,
            "level": 1,
            "event": 1,
            "host": 1,
            "ip": 1
        }
        cursor = collection.find(query, projection).sort(sort_by, sort_direction).skip(skip).limit(page_size)

        logs = []
        async for log in cursor:
            log["_id"] = str(log["_id"])
            logs.append(log)

        logger.info(f"✅ Retrieved {len(logs)} logs for page {page}")
        
        return {
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "logs": logs,
        }
    except Exception as e:
        logger.error(f"❌ Error querying logs: {e}")
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

@app.get("/logs/export")
async def export_logs_as_csv():
    logger.info("📥 CSV export endpoint called")
    
    if collection is None:
        logger.error("❌ Database collection not available for export")
        raise HTTPException(status_code=503, detail="Database not available")
        
    try:
        # You can later apply filters here
        logs_cursor = collection.find().sort("timestamp", -1)
        logs = await logs_cursor.to_list(length=1000)  # Adjust the number as needed
        
        logger.info(f"📊 Found {len(logs)} logs for CSV export")

        if not logs:
            logger.warning("⚠️ No logs found for export")
            raise HTTPException(status_code=404, detail="No logs found")

        # Create CSV manually without pandas
        output = io.StringIO()
        
        if logs:
            # Write CSV header
            headers = list(logs[0].keys())
            logger.info(f"📝 CSV headers: {headers}")
            output.write(','.join(headers) + '\n')
            
            # Write CSV rows
            for log in logs:
                log["_id"] = str(log["_id"])  # Convert ObjectId to string
                row = []
                for header in headers:
                    value = str(log.get(header, ''))
                    # Escape commas and quotes in CSV
                    if ',' in value or '"' in value:
                        value = '"' + value.replace('"', '""') + '"'
                    row.append(value)
                output.write(','.join(row) + '\n')
        
        output.seek(0)
        logger.info("✅ CSV export completed successfully")
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=logs_export.csv"},
        )
    except Exception as e:
        logger.error(f"❌ Error during CSV export: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

# Kafka consumer background task and control
consumer_task = None

def get_kafka_consumer():
    logger.info("🔗 Creating Kafka consumer")
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
        if collection is not None:
            result = await collection.insert_one(log)
            logger.info(f"💾 Saved log with id: {result.inserted_id}")
            logger.debug(f"📄 Log content: {log}")
        else:
            logger.error("❌ Cannot save log: collection not available")
    except Exception as e:
        logger.error(f"❌ Error saving log to MongoDB: {e}")

async def consume_and_store():
    try:
        consumer = get_kafka_consumer()
        logger.info("✅ Kafka consumer connected. Listening for messages...")
        loop = asyncio.get_event_loop()
        
        while True:
            # Poll with timeout to allow task cancellation
            msg_pack = consumer.poll(timeout_ms=1000)
            if not msg_pack:
                await asyncio.sleep(0)  # Yield to event loop
                continue
                
            for tp, messages in msg_pack.items():
                logger.info(f"📦 Received {len(messages)} messages from topic partition {tp}")
                for message in messages:
                    log_data = message.value
                    logger.info(f"📥 Received message: {log_data}")
                    logger.info(f"📋 Message offset: {message.offset}, timestamp: {message.timestamp}")
                    loop.create_task(save_log(log_data))
    except asyncio.CancelledError:
        logger.info("🛑 Kafka consumer task cancelled via asyncio.")
    except Exception as e:
        logger.error(f"❌ Kafka error: {e}")
    finally:
        if 'consumer' in locals():
            consumer.close()
        logger.info("🔌 Kafka consumer closed.")

@app.on_event("startup")
async def startup_event():
    global client, db, collection, consumer_task
    
    logger.info("🚀 FastAPI app is starting up!")
    
    # Initialize MongoDB
    try:
        if MONGODB_URI:
            logger.info("🔗 Connecting to MongoDB...")
            client = AsyncIOMotorClient(MONGODB_URI)
            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]
            
            # Test connection
            await client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully!")
            
            # Log some collection stats
            try:
                doc_count = await collection.count_documents({})
                logger.info(f"📊 Collection '{COLLECTION_NAME}' has {doc_count} documents")
            except Exception as e:
                logger.warning(f"⚠️ Could not get collection stats: {e}")
                
        else:
            logger.warning("⚠️ MONGO_URI not found in environment")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        # Don't fail startup, just log the error
    
    # Start Kafka consumer if explicitly enabled
    enable_kafka = os.getenv("ENABLE_KAFKA", "false").lower()
    logger.info(f"🔍 ENABLE_KAFKA environment variable: {enable_kafka}")
    
    if enable_kafka in ["true", "1", "yes", "on"]:
        try:
            logger.info("🚀 Starting Kafka consumer...")
            consumer_task = asyncio.create_task(consume_and_store())
            logger.info("✅ Kafka consumer task created successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")
    else:
        logger.info("📡 Kafka consumer disabled (set ENABLE_KAFKA=true to enable)")
    
    logger.info("🎉 Startup completed!")

@app.on_event("shutdown")
async def shutdown_event():
    global consumer_task, client
    
    logger.info("🛑 FastAPI app is shutting down...")
    
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        logger.info("✅ Kafka consumer task cancelled gracefully.")
    
    if client:
        client.close()
        logger.info("✅ MongoDB client closed.")
        
    logger.info("👋 Shutdown completed!")

# Add a debugging endpoint to see environment variables (remove in production)
@app.get("/debug/env")
async def debug_env():
    logger.info("📥 Debug env endpoint called")
    return {
        "MONGO_URI_exists": bool(os.getenv("MONGO_URI")),
        "DATABASE_NAME": DATABASE_NAME,
        "COLLECTION_NAME": COLLECTION_NAME,
        "KAFKA_TOPIC": KAFKA_TOPIC,
        "ENABLE_KAFKA": os.getenv("ENABLE_KAFKA", "false"),
        "kafka_consumer_running": consumer_task is not None and not consumer_task.done(),
        "environment_vars": list(os.environ.keys())  # Just the keys, not values for security
    }

# Kafka management endpoints
@app.post("/kafka/start")
async def start_kafka_consumer():
    global consumer_task
    logger.info("📥 Start Kafka consumer endpoint called")
    
    if consumer_task and not consumer_task.done():
        logger.warning("⚠️ Kafka consumer is already running")
        return {"status": "error", "message": "Kafka consumer is already running"}
    
    try:
        logger.info("🚀 Starting Kafka consumer via API...")
        consumer_task = asyncio.create_task(consume_and_store())
        logger.info("✅ Kafka consumer started successfully!")
        return {"status": "success", "message": "Kafka consumer started"}
    except Exception as e:
        logger.error(f"❌ Failed to start Kafka consumer: {e}")
        return {"status": "error", "message": f"Failed to start Kafka consumer: {str(e)}"}

@app.post("/kafka/stop")
async def stop_kafka_consumer():
    global consumer_task
    logger.info("📥 Stop Kafka consumer endpoint called")
    
    if not consumer_task or consumer_task.done():
        logger.warning("⚠️ Kafka consumer is not running")
        return {"status": "error", "message": "Kafka consumer is not running"}
    
    try:
        logger.info("🛑 Stopping Kafka consumer...")
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        consumer_task = None
        logger.info("✅ Kafka consumer stopped successfully!")
        return {"status": "success", "message": "Kafka consumer stopped"}
    except Exception as e:
        logger.error(f"❌ Failed to stop Kafka consumer: {e}")
        return {"status": "error", "message": f"Failed to stop Kafka consumer: {str(e)}"}

@app.get("/kafka/status")
async def kafka_status():
    logger.info("📥 Kafka status endpoint called")
    is_running = consumer_task is not None and not consumer_task.done()
    logger.info(f"📊 Kafka consumer status: {'running' if is_running else 'stopped'}")
    
    return {
        "kafka_consumer_running": is_running,
        "enable_kafka_env": os.getenv("ENABLE_KAFKA", "false"),
        "kafka_config": {
            "topic": KAFKA_TOPIC,
            "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS
        }
    }
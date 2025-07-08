from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import time

# MongoDB Setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["cryptosecure_logs"]  
collection = db["logs"]                 

#Kafka Consumer Setup
consumer = KafkaConsumer(
    'test-logs',
    bootstrap_servers='localhost:50849',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='my-test-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Listening for messages on Kafka and MongoDB\n")

try:
    for message in consumer:
        log_data = message.value
        log_data['received_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

        collection.insert_one(log_data)

        print(f"Stored in MongoDB: {log_data}")

except KeyboardInterrupt:
    print("Keyboard Interrupt.")

finally:
    consumer.close()
    mongo_client.close()

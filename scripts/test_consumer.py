from kafka import KafkaConsumer
import json
import time

consumer = KafkaConsumer(
    'test-logs',
    bootstrap_servers='localhost:50849',
    auto_offset_reset='earliest',
    group_id='my-test-group'
)



print("✅ Connected to Kafka. Listening for messages...\n")

try:
    for message in consumer:
        print(f"📥 Received message: {message.value}")
except KeyboardInterrupt:
    print("\n🛑 Stopped manually.")
finally:
    consumer.close()
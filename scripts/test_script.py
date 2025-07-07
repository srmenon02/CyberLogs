

import json
from kafka import KafkaProducer

try:
    # Create Kafka producer
    producer = KafkaProducer(
        bootstrap_servers='localhost:50849',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("✅ KafkaProducer connected successfully.")
except Exception as e:
    print("❌ Failed to connect KafkaProducer:", e)
    exit(1)

# Define the topic and test message
topic = "test-topic"
test_message = {"event": "test", "status": "ok"}

try:
    print("📤 Sending test message...")
    future = producer.send(topic, test_message)

    # Wait for message to be delivered (or fail)
    result = future.get(timeout=10)
    print("✅ Message sent successfully to:", result.topic, "partition:", result.partition)
except Exception as e:
    print("❌ Failed to send message:", e)

producer.flush()
producer.close()

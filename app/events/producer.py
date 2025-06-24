from kafka import KafkaProducer
import json
import os

def get_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all'  # Ensure message reliability
    )

# Singleton pattern (optional)
producer = get_producer()

def send_inventory_event(event_type: str, item_data: dict):
    event = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        **item_data
    }
    producer.send('inventory_updates', event)
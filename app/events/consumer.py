from kafka import KafkaConsumer
import json
import os
from ..models import InventoryItem
from ..database import SessionLocal

def start_consumer():
    consumer = KafkaConsumer(
        'inventory_updates',
        bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='inventory-group'
    )

    db = SessionLocal()
    
    for message in consumer:
        try:
            event = message.value
            print(f"Processing event: {event}")
            
            # Example event handling
            if event['event_type'] == 'item_created':
                item = db.query(InventoryItem).filter(
                    InventoryItem.id == event['item_id']
                ).first()
                print(f"New item added: {item.name}")
                
            elif event['event_type'] == 'stock_updated':
                # Add your business logic
                pass
                
        except Exception as e:
            print(f"Error processing message: {e}")
        finally:
            db.close()

if __name__ == "__main__":
    start_consumer()
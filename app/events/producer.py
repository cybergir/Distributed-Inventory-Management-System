from confluent_kafka import Producer
import json

conf = {'bootstrap.servers': 'kafka:9092'}
producer = Producer(conf)

def send_inventory_update(product_id, warehouse_id, delta):
    event = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "delta": delta
    }
    producer.produce("inventory_updates", json.dumps(event))
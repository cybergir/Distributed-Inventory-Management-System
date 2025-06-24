import redis
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from dotenv import load_dotenv
import os
from kafka import KafkaProducer


load_dotenv()

app = FastAPI()


# Database setup
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

r = redis.Redis(
    host='redis',
    port=6379,
    db=0,
    decode_responses=True
)

# Kafka producer
kafka_producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    quantity = Column(Integer)
    location = Column(String(50))  # Warehouse location

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "location": self.location
        }

Base.metadata.create_all(bind=engine)

class ItemCreate(BaseModel):
    name: str
    quantity: int
    location: str

@app.post("/items/")
def create_item(item: ItemCreate, db=Depends(get_db)):
    db_item = InventoryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Send Kafka event
    kafka_producer.send('inventory_updates', {
        'event': 'item_created',
        'item_id': db_item.id,
        'name': db_item.name
    })

    r.delete(f"item_{db_item.id}") 
    
    return db_item

@app.get("/items/{item_id}")
def read_item(item_id: int, db=Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/cached-items/{item_id}")
def get_cached_item(item_id: int, db=Depends(get_db)):
    """
    Checks Redis cache first:
    - Returns cached data if available
    - Falls back to database if not
    - Caches database results for 1 hour (3600 seconds)
    """
    # 1. Check Redis cache
    cache_key = f"item_{item_id}"
    cached = r.get(cache_key)
    if cached:
        return {"source": "cache", "data": json.loads(cached)}
    
    # 2. Query Database if not in cache
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # 3. Cache the result
    r.setex(
        cache_key,
        3600,  # 1 hour TTL
        json.dumps(item.to_dict())  # Serialize to JSON
    )
    
    return {"source": "database", "data": item.to_dict()}
# Enable CORS (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "running", "system": "Distributed Inventory Management"}

@app.get("/inventory/{product_id}")
def get_inventory(product_id: int):
    """Sample inventory endpoint"""
    return {
        "product_id": product_id,
        "stock": 100,  # Replace with real data
        "locations": ["Warehouse A", "Warehouse B"]
    }
@app.get("/test-db")
def test_db():
    try:
        db = SessionLocal()
        result = db.execute("SELECT 1")
        db.close()
        return {"status": "Database connected!", "result": str(result.fetchone())}
    except Exception as e:
        return {"error": str(e)}
@app.get("/warehouse/{location}")
def get_warehouse_items(location: str, db=Depends(get_db)):
    items = db.query(InventoryItem).filter(InventoryItem.location == location).all()
    return {"location": location, "items": items}
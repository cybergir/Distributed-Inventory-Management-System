from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
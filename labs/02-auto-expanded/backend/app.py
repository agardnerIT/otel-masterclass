import os
import requests

INVENTORY_URL = os.getenv("INVENTORY_URL", "http://localhost:8002")

"""The backend service. There is no OpenTelemetry code in this file on purpose."""
import time

from fastapi import FastAPI, HTTPException, Request



app = FastAPI()

PRODUCTS = {
    1: {"name": "keyboard", "price": 49.0},
    2: {"name": "mouse", "price": 25.0},
}


@app.get("/products/{product_id}")
def get_product(product_id: int, request: Request):
    # The header that the frontend sent. It carries the trace context.
    print("backend received traceparent:", request.headers.get("traceparent"), flush=True)
    time.sleep(0.05)  # pretend to do some work
    if product_id == 13:
        raise RuntimeError("the database is down")  # becomes a 500 error
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="product not found")
    stock = requests.get(f"{INVENTORY_URL}/stock/{product_id}", timeout=5).json()
    return {**PRODUCTS[product_id], "in_stock": stock["in_stock"]}

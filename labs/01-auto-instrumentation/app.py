"""A small shop API. There is no OpenTelemetry code in this file on purpose."""
import time

from fastapi import FastAPI, HTTPException

app = FastAPI()

PRODUCTS = {
    1: {"name": "keyboard", "price": 49.0},
    2: {"name": "mouse", "price": 25.0},
}


@app.get("/")
def home():
    return {"message": "hello"}


@app.get("/products/{product_id}")
def get_product(product_id: int):
    time.sleep(0.05)  # pretend to do some work
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="product not found")
    return PRODUCTS[product_id]

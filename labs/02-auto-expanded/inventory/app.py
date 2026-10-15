"""The inventory service (for the "add a third hop" exercise).
There is no OpenTelemetry code in this file on purpose."""
import time

from fastapi import FastAPI, Request

app = FastAPI()

STOCK = {1: 12, 2: 0}


@app.get("/stock/{product_id}")
def get_stock(product_id: int, request: Request):
    print("inventory received traceparent:", request.headers.get("traceparent"), flush=True)
    time.sleep(0.03)  # pretend to do some work
    return {"product_id": product_id, "in_stock": STOCK.get(product_id, 0)}

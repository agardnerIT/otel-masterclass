"""The frontend service. Same as Lab 02, with a quantity. No OpenTelemetry code on purpose."""
import os

import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")


@app.get("/order/{product_id}")
def order(product_id: int, quantity: int = 1):
    response = requests.get(
        f"{BACKEND_URL}/orders/{product_id}", params={"quantity": quantity}, timeout=5
    )
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="no such product")
    if response.status_code == 402:
        raise HTTPException(status_code=402, detail="payment declined")
    if response.status_code >= 500:
        raise HTTPException(status_code=502, detail="backend failed")
    return response.json()

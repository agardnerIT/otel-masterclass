"""The frontend service. It calls the backend with requests.
There is no OpenTelemetry code in this file on purpose."""
import os

import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")


@app.get("/order/{product_id}")
def order(product_id: int):
    response = requests.get(f"{BACKEND_URL}/products/{product_id}", timeout=5)
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="no such product")
    if response.status_code >= 500:
        raise HTTPException(status_code=502, detail="backend failed")
    # response.request is the request that was really sent.
    # The instrumentation added the traceparent header to it.
    sent = response.request.headers.get("traceparent")
    print("frontend sent traceparent:", sent, flush=True)
    return {"product": response.json(), "traceparent_sent": sent}

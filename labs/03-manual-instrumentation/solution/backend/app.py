"""The backend service with manual instrumentation (solution)."""
import logging
import random
import time
import uuid

from fastapi import FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode

app = FastAPI()

# The agent (opentelemetry-instrument) sets up the SDK. We only use the API here.
tracer = trace.get_tracer("shop.backend")
meter = metrics.get_meter("shop.backend")
logger = logging.getLogger("shop.backend")
logger.setLevel(logging.INFO)

# Metrics are created once, when the app starts.
orders_counter = meter.create_counter(
    "shop.orders", unit="{order}", description="Number of orders"
)
order_value_histogram = meter.create_histogram(
    "shop.order.value", unit="USD", description="Value of each order"
)

PRODUCTS = {
    1: {"name": "keyboard", "price": 49.0},
    2: {"name": "mouse", "price": 25.0},
    3: {"name": "monitor", "price": 300.0},
}

PAYMENT_LIMIT = 500.0


class PaymentDeclined(Exception):
    pass


def charge_payment(order_value: float) -> None:
    time.sleep(random.uniform(0.02, 0.08))  # pretend to call a payment provider
    if order_value > PAYMENT_LIMIT:
        raise PaymentDeclined(f"amount {order_value:.2f} is over the limit")


@app.get("/orders/{product_id}")
def create_order(product_id: int, quantity: int = 1):
    product = PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")

    order_id = uuid.uuid4().hex[:8]
    order_value = product["price"] * quantity
    declined = False

    # A custom span. It is a child of the FastAPI server span.
    with tracer.start_as_current_span("process_order") as span:
        # Attributes: business data on the span.
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.quantity", quantity)
        span.set_attribute("order.value", order_value)
        span.set_attribute("product.name", product["name"])

        # An event: a point in time inside the span.
        span.add_event("stock.checked", {"stock.available": True})

        # Exercise 2: a span just for the payment call.
        with tracer.start_as_current_span("charge_payment") as payment_span:
            payment_span.set_attribute("payment.amount", order_value)
            try:
                charge_payment(order_value)
            except PaymentDeclined as exc:
                # Record the error by hand: an exception event and an ERROR status.
                payment_span.record_exception(exc)
                payment_span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.set_status(Status(StatusCode.ERROR, "payment declined"))
                declined = True

        # This log line is inside the span, so it gets the trace ID and span ID.
        if declined:
            logger.error("order %s declined, value %.2f", order_id, order_value)
        else:
            logger.info("order %s accepted, value %.2f", order_id, order_value)

    # Metrics. Keep attribute values to a small set. Never use order.id or a user ID here.
    outcome = "declined" if declined else "paid"
    orders_counter.add(1, {"product.name": product["name"], "order.outcome": outcome})
    if not declined:
        order_value_histogram.record(order_value, {"product.name": product["name"]})

    if declined:
        raise HTTPException(status_code=402, detail="payment declined")
    return {"order_id": order_id, "product": product["name"], "value": order_value}

from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST, Gauge
from fastapi.responses import Response
import os
import time

app = FastAPI()

# PROMETHEUS METRICS
login_counter = Counter("login_requests_total", "Total number of login requests")
health_check_counter = Counter("health_checks_total", "Total number of health checks")

# Additional Prometheus metrics
response_time_gauge = Gauge("response_time_seconds", "Response time in seconds")
memory_usage_gauge = Gauge("memory_usage_bytes", "Memory usage in bytes")
cpu_usage_gauge = Gauge("cpu_usage_percent", "CPU usage percentage")

class LoginRequest(BaseModel):
    username: str
    password: str

@app.middleware("http")
async def prometheus_metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process = os.getpid()
    memory_usage = os.popen(f"ps -o rss= -p {process}").read().strip()
    cpu_usage = os.popen(f"ps -o %cpu= -p {process}").read().strip()

    response_time_gauge.set(time.time() - start_time)
    memory_usage_gauge.set(int(memory_usage) * 1024)  # Convert KB to bytes
    cpu_usage_gauge.set(float(cpu_usage))

    return response

@app.post("/login")
def login(req: LoginRequest):
    login_counter.inc()
    if req.username == "admin" and req.password == "password":
        return {"status": "success", "token": "demo-token"}
    return {"status": "error", "message": "Invalid credentials"}

@app.get("/")
def root():
    return {"message": "Demo login microservice is running!"}

@app.get("/health")
def health():
    health_check_counter.inc()
    return {"status": "healthy"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

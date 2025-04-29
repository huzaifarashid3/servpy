from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime, timezone
import os
import json
import socket
import docker
from prometheus_client import start_http_server, Counter, Gauge
import threading

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allow CORS (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track running containers
running_containers = {}

# Prometheus metrics
request_counter = Counter("requests_total", "Total number of requests")
response_time_gauge = Gauge("response_time_seconds", "Response time in seconds")
memory_usage_gauge = Gauge("memory_usage_bytes", "Memory usage in bytes")
cpu_usage_gauge = Gauge("cpu_usage_percent", "CPU usage percentage")

# Start Prometheus metrics server
threading.Thread(target=start_http_server, args=(8001,), daemon=True).start()

@app.middleware("http")
async def prometheus_metrics_middleware(request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process = os.getpid()
    memory_usage = os.popen(f"ps -o rss= -p {process}").read().strip()
    cpu_usage = os.popen(f"ps -o %cpu= -p {process}").read().strip()

    request_counter.inc()
    response_time_gauge.set(time.time() - start_time)
    memory_usage_gauge.set(int(memory_usage) * 1024)  # Convert KB to bytes
    cpu_usage_gauge.set(float(cpu_usage))

    return response

def get_available_port():
    """Find an available port."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@app.get("/")
def read_root():
    return {"message": "Backend is running!"}


@app.post("/upload-microservice")
async def upload_microservice(
    name: str = Form(...),
    description: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Upload a new microservice with files."""
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        ms_dir = os.path.join(UPLOAD_DIR, f"{name}_{timestamp}")
        os.makedirs(ms_dir, exist_ok=True)

        saved_files = []
        for file in files:
            file_path = os.path.join(ms_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            saved_files.append(file.filename)

        metadata = {"name": name, "description": description, "files": saved_files}
        with open(os.path.join(ms_dir, "metadata.json"), "w") as meta_file:
            json.dump(metadata, meta_file)

        return JSONResponse({
            "status": "success",
            "microservice": name,
            "description": description,
            "files": saved_files
        })
    except Exception as e:
        return JSONResponse(
            {"status": "error", "detail": str(e)},
            status_code=500
        )


def get_microservice_metadata(ms_dir):
    meta_path = os.path.join(ms_dir, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return json.load(f)
    # fallback
    return {
        "name": os.path.basename(ms_dir).rsplit("_", 1)[0],
        "description": "",
        "files": [f for f in os.listdir(ms_dir) if f != "metadata.json"]
    }


@app.get("/list-microservices")
def list_microservices():
    """List all uploaded microservices."""
    microservices = []
    for folder in os.listdir(UPLOAD_DIR):
        ms_dir = os.path.join(UPLOAD_DIR, folder)
        if os.path.isdir(ms_dir):
            meta = get_microservice_metadata(ms_dir)
            meta["folder"] = folder
            microservices.append(meta)
    return {"microservices": microservices}


@app.get("/download/{folder}/{filename}")
def download_file(folder: str, filename: str):
    """Download a specific file from a microservice."""
    file_path = os.path.join(UPLOAD_DIR, folder, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, filename=filename)


@app.post("/start-microservice/{folder}")
def start_microservice(folder: str):
    """Start a Docker container for a microservice."""
    ms_dir = os.path.join(UPLOAD_DIR, folder)
    dockerfile_path = os.path.join(ms_dir, "Dockerfile")

    if not os.path.isfile(dockerfile_path):
        raise HTTPException(status_code=404, detail="Dockerfile not found.")

    client = docker.from_env()
    image_tag = f"microservice_{folder.lower()}"
    container_name = f"ms_{folder}"

    try:
        # Stop existing container if present
        try:
            existing = client.containers.get(container_name)
            existing.stop()
            existing.remove()
        except docker.errors.NotFound:
            pass

        # Build image
        image, _ = client.images.build(path=ms_dir, tag=image_tag)

        # Run container
        port = get_available_port()
        container = client.containers.run(
            image=image_tag,
            detach=True,
            ports={"8000/tcp": port},
            name=container_name,
            remove=True
        )

        running_containers[folder] = {"id": container.id, "port": port}
        return {"status": "started", "container_id": container.id, "port": port}

    except docker.errors.BuildError as e:
        raise HTTPException(status_code=500, detail=f"Docker build failed: {e}")
    except docker.errors.ContainerError as e:
        raise HTTPException(status_code=500, detail=f"Container run failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-microservice/{folder}")
def stop_microservice(folder: str):
    """Stop a running microservice container."""
    client = docker.from_env()
    info = running_containers.get(folder)

    if not info:
        raise HTTPException(status_code=404, detail="Microservice not running.")

    try:
        container = client.containers.get(info["id"])
        container.stop()
        del running_containers[folder]
        return {"status": "stopped"}
    except docker.errors.NotFound:
        del running_containers[folder]
        raise HTTPException(status_code=404, detail="Container not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status-microservices")
def status_microservices():
    """Return status of all running microservices."""
    return {"running": running_containers}

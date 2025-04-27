from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
from datetime import datetime, timezone
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import json
import io
import zipfile
import docker

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory tracking of running containers: {folder: container_id}
running_containers = {}


def get_available_port():
    # Find an available port (simple version, for demo)
    import socket

    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@app.get("/")
def read_root():
    return {"message": "Backend is up!"}


@app.post("/upload-microservice")
async def upload_microservice(
    name: str = Form(...),
    description: str = Form(...),
    files: List[UploadFile] = File(...),
):
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        ms_dir = os.path.join(UPLOAD_DIR, f"{name}_{timestamp}")
        os.makedirs(ms_dir, exist_ok=True)
        saved_files = []
        for file in files:
            file_path = os.path.join(ms_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_files.append(file.filename)
        # Save metadata
        metadata = {"name": name, "description": description, "files": saved_files}
        meta_path = os.path.join(ms_dir, "metadata.json")
        with open(meta_path, "w") as meta_file:
            json.dump(metadata, meta_file)
        return JSONResponse(
            {
                "status": "success",
                "microservice": name,
                "description": description,
                "files": saved_files,
            }
        )
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


def get_microservice_metadata(ms_dir):
    meta_path = os.path.join(ms_dir, "metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return json.load(f)
    # Fallback: infer from folder name
    name = os.path.basename(ms_dir).rsplit("_", 1)[0]
    return {"name": name, "description": "", "files": os.listdir(ms_dir)}


@app.get("/list-microservices")
def list_microservices():
    microservices = []
    for ms_folder in os.listdir(UPLOAD_DIR):
        ms_dir = os.path.join(UPLOAD_DIR, ms_folder)
        if os.path.isdir(ms_dir):
            meta = get_microservice_metadata(ms_dir)
            meta["folder"] = ms_folder
            meta["files"] = [f for f in os.listdir(ms_dir) if f != "metadata.json"]
            microservices.append(meta)
    return JSONResponse({"microservices": microservices})


@app.get("/download/{folder}/{filename}")
def download_file(folder: str, filename: str):
    file_path = os.path.join(UPLOAD_DIR, folder, filename)
    if not os.path.isfile(file_path):
        return JSONResponse(
            {"status": "error", "detail": "File not found"}, status_code=404
        )
    return FileResponse(file_path, filename=filename)


@app.post("/start-microservice/{folder}")
def start_microservice(folder: str):
    ms_dir = os.path.join(UPLOAD_DIR, folder)
    dockerfile_path = os.path.join(ms_dir, "Dockerfile")
    if not os.path.isfile(dockerfile_path):
        raise HTTPException(
            status_code=404, detail="Dockerfile not found in microservice folder."
        )
    client = docker.from_env()
    image_tag = f"microservice_{folder.lower()}"
    try:
        # Build image
        image, _ = client.images.build(path=ms_dir, tag=image_tag)
        # Run container
        port = get_available_port()
        container = client.containers.run(
            image=image_tag,
            detach=True,
            ports={"8000/tcp": port},
            name=f"ms_{folder}",
            remove=True,
        )
        running_containers[folder] = {"id": container.id, "port": port}
        return {"status": "started", "container_id": container.id, "port": port}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-microservice/{folder}")
def stop_microservice(folder: str):
    client = docker.from_env()
    info = running_containers.get(folder)
    if not info:
        raise HTTPException(status_code=404, detail="Microservice is not running.")
    try:
        container = client.containers.get(info["id"])
        container.stop()
        del running_containers[folder]
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status-microservices")
def status_microservices():
    # Return running microservices and their ports
    return {"running": running_containers}

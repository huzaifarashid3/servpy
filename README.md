# HackOps: Microservice Sharing Platform

## Overview
HackOps is a DevOps-focused web platform for uploading, sharing, running, and testing reusable microservices. Users can upload microservices (e.g., login, random number generator), run them in isolated Docker containers, and test their API endpoints—all from a modern web UI. The project demonstrates best practices in DevOps, CI/CD, containerization, monitoring, and automation.

---

## Features
- **Upload Microservices:** Upload code (Dockerfile, app.py, requirements.txt) for reusable microservices.
- **Run in Docker:** Start/stop uploaded microservices in isolated Docker containers from the web UI.
- **API Testing:** Test endpoints of running microservices directly from the frontend.
- **Download Files:** Download individual files from any uploaded microservice.
- **List & Manage:** View all uploaded microservices, see their status, and manage them.
- **Monitoring:** Prometheus and Grafana included for monitoring and observability.
- **CI/CD:** Automated testing, building, and deployment using GitHub Actions and Amazon ECR.

---

## Project Structure
```
served/
├── backend/           # FastAPI backend (microservice management, Docker control)
├── frontend/          # React frontend (UI, API tester)
├── uploads/           # Uploaded microservices (each in its own folder)
├── docker-compose.yml # Orchestrates all services
├── prometheus.yml     # Prometheus config
├── .github/workflows/ # CI/CD pipelines
└── README.md
```

---

## Local Setup & Usage

### 1. Prerequisites
- Docker & Docker Compose
- Node.js (v20+) and npm (for local frontend dev)
- Python 3.11+ (for local backend dev)

### 2. Clone the Repository
```sh
git clone <your-repo-url>
cd served
```

### 3. Run Everything with Docker Compose
```sh
docker-compose up --build
```
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### 4. Manual Dev (Optional)
- **Backend:**
  ```sh
  cd backend
  python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  uvicorn main:app --reload
  ```
- **Frontend:**
  ```sh
  cd frontend
  npm install
  npm run dev
  ```

---

## CI/CD Pipeline (GitHub Actions)

### 1. Continuous Integration
- **Backend:**
  - Installs dependencies
  - Runs unit tests with pytest
  - Runs integration tests (spins up services with Docker Compose and tests endpoints)
- **Frontend:**
  - Installs dependencies
  - Runs React/Vitest tests
- **Docker:**
  - Builds backend and frontend Docker images to ensure Dockerfiles are valid

### 2. Continuous Deployment
- **Amazon ECR:**
  - On every push to `main`, builds and tags Docker images for backend and frontend
  - Pushes images to Amazon ECR (both `latest` and commit SHA tags)
- **Secrets Required:**
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
  - `ECR_BACKEND_REPO`, `ECR_FRONTEND_REPO`

### 3. Example Workflow Steps
```
- Checkout code
- Set up Python & Node.js
- Install backend/frontend dependencies
- Run backend & frontend tests
- Build Docker images
- Run integration tests with Docker Compose
- Push images to Amazon ECR
```

---

## Continuous Deployment with AWS Copilot

### Copilot & AWS ECS Structure
- **Copilot Directory:** All Copilot configuration is stored in the `copilot/` folder. Each service (backend, frontend, grafana, prometheus) and environment (e.g., dev) has its own `manifest.yml`.
- **Services:**
  - `frontend`: Load Balanced Web Service (public)
  - `backend`: Load Balanced Web Service (public or private)
  - `grafana`: Load Balanced Web Service (public)
  - `prometheus`: Backend Service (private)
- **Environments:**
  - `dev`: Default environment for development and testing

### Deployment Flow
1. **Build & Push Images:**
   - GitHub Actions builds Docker images for backend and frontend and pushes them to Amazon ECR (tagged as `latest` and with the commit SHA).
2. **Copilot Deploy:**
   - The workflow runs `copilot deploy --yes` to update all ECS services with the latest images and configuration.
3. **AWS ECS Structure:**
   - Each service runs as an ECS service in the Copilot-managed cluster.
   - Load balancers are automatically created for public services (frontend, backend, grafana).
   - Prometheus runs as a private backend service for internal monitoring.
   - Networking, IAM, and scaling are managed by Copilot.

### How to Access
- **Frontend:** Public URL provided by Copilot/ALB
- **Backend:** Public or internal URL (depending on manifest)
- **Grafana:** Public URL (secured by password)
- **Prometheus:** Internal URL (for monitoring only)

### Copilot Directory Example
```
copilot/
├── backend/manifest.yml
├── frontend/manifest.yml
├── grafana/manifest.yml
├── prometheus/manifest.yml
└── environments/
    └── dev/manifest.yml
```

### GitHub Actions Workflow
- On every push to `main`, the workflow:
  1. Builds and pushes Docker images to ECR
  2. Runs `copilot deploy --yes` to update ECS services
- AWS credentials and ECR repo URLs are managed via GitHub secrets

---

## Monitoring & Observability
- **Prometheus** scrapes metrics from services (add `/metrics` endpoints as needed)
- **Grafana** for dashboards and visualization (default login: admin/admin)

---

## Example Microservices
- **Login Service:** `/uploads/demo_login_20250427/`
- **Random Number Generator:** `/uploads/random_number_20250427/`

---

## DevOps Best Practices Demonstrated
- Dockerized microservices and platform
- Automated CI/CD with GitHub Actions
- Integration and unit testing
- Infrastructure as code (Docker Compose)
- Monitoring with Prometheus & Grafana
- Secure, automated image deployment to ECR

---

## Authors & Credits
- Team HackOps
- Built for DevOps Hackathon 2025

---

## License
MIT

# BioMedGraphica Server Setup & Run Instructions

## 🧰 Prerequisites

Ensure the following are installed:

- Python **3.10+**
- [Docker](https://www.docker.com/) (for Redis)
- Required Python packages (`requirements.txt`)

## 📦 Installation

```bash
git clone https://github.com/your-org/BioMedGraphica.git
cd BioMedGraphica
pip install -r requirements.txt
```

## 🚀 Running the Application

### 1. Start Redis (via Docker)

```bash
docker run -d -p 6379:6379 redis
```

### 2. Start FastAPI Backend

```bash
uvicorn backend.api.main:app --reload
```

### 3. Start Celery Worker

```bash
# On Windows:
celery -A backend.celery_worker worker --loglevel=info --pool=solo

# On Linux/macOS:
celery -A backend.celery_worker worker --loglevel=info
```

### 4. Start Streamlit App

```bash
streamlit run app.py
```

---

## 🌐 Accessing the App

- Local: [http://localhost:8501](http://localhost:8501)  
- Network: `http://<your-ip>:8501`

---

## ✨ Features

- Upload & configure biomedical entity files
- Hard & soft match integration
- Real-time task tracking via Redis
- Final export: `.npy`, `.csv`, `.zip` output

---

## 🧩 Project Structure

```
BioMedGraphica/
├── app.py                  # Streamlit frontend
├── backend/
│   ├── api/                # FastAPI endpoints
│   │   └── main.py
│   ├── tasks/              # Celery tasks
│   ├── service/            # Core logic
│   ├── config.py
│   └── celery_worker.py
├── requirements.txt
└── README.md
```

---

## 🛠️ Troubleshooting

- **Redis connection refused**: Make sure Redis is running on port `6379`
- **Celery not responding**: Confirm both Redis and Celery are running
- **Firewall issues**: Open necessary ports (`6379`, `8000`, `8501`)

---

## 📌 Notes

- Use `--reload` for development only
- For production: disable reload and run via Gunicorn + Uvicorn workers

---

## ✅ Health Check

Test the backend:

```bash
curl http://localhost:8000/health
# {"status": "healthy", "message": "BioMedGraphica Backend API is running"}
```

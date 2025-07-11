# 🚀 Installation Guide

This document provides instructions for running the project both locally and in production.

---

## ✅ Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 15+ (optional locally if not using Docker)
- Git

---

## 🔧 Local Setup (using Docker)

1. **Clone the repository:**

```bash
git clone https://github.com/your-org/lobby_backend.git
cd lobby_backend
```

2. **Create `.env` file:**

```env
POSTGRES_DB=your_db_name
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
SECRET_KEY=your_django_secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

3. **Run Docker Compose:**

```bash
docker-compose up --build
```

4. **Apply migrations and load fixtures (optional):**

```bash
docker-compose exec lobby python manage.py migrate
docker-compose exec lobby python manage.py loaddata test_db_data/user.json
```

5. **Access the app:**

- Backend: `http://localhost:8000`
- Admin panel: `http://localhost:8000/admin`

---

## 🌐 Server Deployment (Production)

1. **Set up server (Ubuntu recommended):**
   - Install Docker & Docker Compose
   - Set up firewall rules
   - Install Nginx

2. **Clone project & configure .env:**

Same `.env` as above, but use production values and set `DEBUG=False`.

3. **Build and run in production mode:**

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

4. **Set up static file collection:**

```bash
docker-compose exec lobby python manage.py collectstatic --noinput
```

5. **Configure Nginx:**

Point it to proxy requests to the Gunicorn app inside the container (port 8000).

6. **Use a process manager (optional):**
   - You can use `systemd` or `supervisord` for restart policies.

---

## 🧪 Optional: Load Test Data

```bash
docker-compose exec lobby python manage.py load_test_data
```

---

## 📬 Email Configuration (for password reset)

Configure SMTP settings in `.env`:

```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=your_email
```

---

## ❓ Troubleshooting

- Make sure Docker volumes are mounted correctly
- Use `docker-compose logs` to debug
- Ensure PostgreSQL is reachable and credentials are valid

---

Happy coding!
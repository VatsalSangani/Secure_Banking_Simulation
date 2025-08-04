# 💳 Secure Banking Backend Simulation

This project is a **Python-based secure banking backend** that simulates core features of an online banking system. It includes OTP-based authentication, rate limiting on sensitive routes, account lockout mechanisms, and more — designed with security and extensibility in mind.

---

## 🚀 Features

- ✅ **User Registration & Login**
- 🔐 **OTP Authentication** (One-Time Password)
- 🔁 **Resend OTP with Expiry Control**
- 🚫 **Rate Limiting** for sensitive endpoints
- 🔒 **Temporary Account Lockout** after multiple failed OTP attempts
- ⚙️ Modular design for easy extension

---

## 🛠️ Tech Stack

- **FastAPI** – High-performance Python web framework
- **Pydantic** – Data validation and settings management
- **Redis** – For OTP expiry & rate limiting (optional)
- **Docker** – For containerized deployment
- **Pytest** – For testing

---

## 🧪 Running Locally

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/secure-banking-backend.git
cd secure-banking-backend
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
uvicorn app.main:app --reload
```
The backend will be live at: http://127.0.0.1:8000

---

## 🐳 Docker (Optional)
Build & Run with Docker:
```bash
docker build -t secure-banking .
docker run -d -p 8000:8000 secure-banking
```

## 🧪 API Testing
You can test all routes using the built-in Swagger UI at:

```bash
http://127.0.0.1:8000/docs
```

---


## 📌 Coming Soon
A secure and modern frontend UI (React + Tailwind) is in development to interact with this backend. Stay tuned!

---

## 🤝 Contributing
Feel free to fork the project and submit PRs. Open to improvements, feature requests, and suggestions.

---

##📄 License
MIT License – feel free to use and adapt.

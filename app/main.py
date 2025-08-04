from fastapi import FastAPI
from app.api.endpoints import auth, accounts, transactions, otp
from app.api.endpoints import deposit as deposit_router
from app.db.session import engine
from app.db.base import Base
from app.models import *  # ensures models are registered
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Secure Banking Backend API",
    description="A secure banking system simulation built with FastAPI, JWT, PostgreSQL, and Docker.",
    version="1.0.0"
)

# Register API routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(otp.router, tags=["OTP"])
app.include_router(deposit_router.router, prefix="/deposit", tags=["Deposit"])

# ────────────────────────────────
# Swagger JWT Auth Support
# ────────────────────────────────
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

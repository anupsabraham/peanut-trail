from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, statements, transactions

app = FastAPI(title="FinancePlan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Check the status of the service."""
    return {"status": "ok"}


app.include_router(analytics.router)
app.include_router(statements.router)
app.include_router(transactions.router)

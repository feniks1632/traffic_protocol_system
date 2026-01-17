from fastapi import FastAPI
from backend.routers import (
    auth,
    owners,
    inspectors,
    vehicles,
    protocols,
    violations,
    lock,
    reports
)

app = FastAPI(title="Система контроля правонарушений")

app.include_router(reports.router, prefix="/reports")
app.include_router(lock.router)
app.include_router(auth.router)
app.include_router(owners.router, prefix="/owners")
app.include_router(inspectors.router, prefix="/inspectors")
app.include_router(vehicles.router, prefix="/vehicles")
app.include_router(protocols.router, prefix="/protocols")
app.include_router(violations.router, prefix="/violations")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.system import router as system_router
from app.auth.router import router as auth_router
from app.api.clients import router as clients_router
from app.api.processes import router as processes_router
from app.api.deadlines import router as deadlines_router
from app.api.offices import router as offices_router

import app.models  # noqa

app = FastAPI(title="Juris AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(processes_router)
app.include_router(deadlines_router)
app.include_router(offices_router)


@app.get("/")
def root():
    return {"status": "ok"}

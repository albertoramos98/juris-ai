from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.database import Base, engine

# IMPORTA OS MODELS PARA REGISTRAR NO Base.metadata
from app.models.user import User  # noqa: F401
from app.models.office import Office  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.process import Process  # noqa: F401
from app.models.deadline import Deadline  # noqa: F401
from app.models.office_override import OfficeOverride  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.email_flow import EmailFlow  # noqa: F401
from app.models.global_knowledge import GlobalKnowledge  # noqa: F401
from app.models.process_event import ProcessEvent  # noqa: F401

from app.core.settings import settings
from app.jobs.email_scheduler import start_email_scheduler, stop_email_scheduler

# Roteadores
from app.api.system import router as system_router
from app.auth.router import router as auth_router
from app.api.clients import router as clients_router
from app.api.processes import router as processes_router
from app.api.deadlines import router as deadlines_router
from app.api.offices import router as offices_router
from app.auth.google import router as google_router
from app.api.google_drive import router as google_drive_router
from app.api.google_calendar import router as google_calendar_router
from app.api.documents import router as documents_router
from app.api.imports import router as imports_router
from app.api.emails import router as emails_router
from app.api.email_flows import router as email_flows_router
from app.api.users import router as users_router
from app.api.rag import router as rag_router
from app.api.meetings import router as meetings_router
from app.api.styles import router as styles_router
from app.api.global_knowledge import router as global_knowledge_router

app = FastAPI(title="Juris AI")

@app.on_event("startup")
def on_startup():
    # 1) garante schema
    Base.metadata.create_all(bind=engine)
    # 2) sobe scheduler
    start_email_scheduler()

@app.on_event("shutdown")
def on_shutdown():
    stop_email_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos Roteadores
app.include_router(system_router)
app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(processes_router)
app.include_router(deadlines_router)
app.include_router(offices_router)
app.include_router(google_router)
app.include_router(google_drive_router)
app.include_router(google_calendar_router)
app.include_router(documents_router)
app.include_router(imports_router)
app.include_router(emails_router)
app.include_router(email_flows_router)
app.include_router(users_router)
app.include_router(rag_router)
app.include_router(meetings_router)
app.include_router(styles_router)
app.include_router(global_knowledge_router)

@app.get("/")
def root():
    return {"status": "ok"}

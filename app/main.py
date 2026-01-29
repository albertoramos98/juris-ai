from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine

# IMPORTA OS MODELS PARA REGISTRAR NO Base.metadata
# (sem isso, create_all pode não criar nada)
from app.models.user import User  # noqa: F401
from app.models.office import Office  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.process import Process  # noqa: F401
from app.models.deadline import Deadline  # noqa: F401
from app.models.office_override import OfficeOverride  # noqa: F401
from app.api.google_drive import router as google_drive_router
from app.api.google_calendar import router as google_calendar_router
from app.core.settings import settings
print("SMTP CHECK:", settings.smtp_host, settings.smtp_port, settings.smtp_from)
from app.api.system import router as system_router
from app.auth.router import router as auth_router
from app.api.clients import router as clients_router
from app.api.processes import router as processes_router
from app.api.deadlines import router as deadlines_router
from app.api.offices import router as offices_router
from app.auth.google import router as google_router
from app.api.documents import router as documents_router
from app.api.imports import router as imports_router
from app.api.emails import router as emails_router



app = FastAPI(title="Juris AI")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


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
app.include_router(google_router)
app.include_router(google_drive_router)
app.include_router(google_calendar_router)
app.include_router(documents_router)
app.include_router(imports_router)
app.include_router(emails_router)


@app.get("/")
def root():
    return {"status": "ok"}

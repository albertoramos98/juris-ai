# Importa todos os models para registrar no SQLAlchemy
from app.models.office import Office  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.client import Client  # noqa: F401
from app.models.process import Process  # noqa: F401
from app.models.deadline import Deadline  # noqa: F401
from app.models.user_block import UserBlock  # noqa: F401
from app.models.office_override import OfficeOverride  # noqa: F401
from app.models.google_token import GoogleToken  # noqa: F401
from .document import Document


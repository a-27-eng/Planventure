from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .trip import Trip

__all__ = ['db', 'User', 'Trip']
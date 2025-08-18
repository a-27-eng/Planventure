from .password_utils import PasswordUtils
from .jwt_utils import JWTUtils
from .itinerary_generator import ItineraryGenerator
from flask_jwt_extended import get_jwt_identity

def get_current_user_id():
    """Get current user ID from JWT token."""
    try:
        user_id_str = get_jwt_identity()
        if user_id_str:
            return int(user_id_str)
        return None
    except (ValueError, TypeError):
        return None
    except Exception:
        return None

__all__ = ['PasswordUtils', 'JWTUtils', 'ItineraryGenerator', 'get_current_user_id']
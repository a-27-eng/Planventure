from datetime import datetime, date
from . import db
import json
from utils.itinerary_generator import ItineraryGenerator

class Trip(db.Model):
    __tablename__ = 'trips'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='planned', nullable=False)
    itinerary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('trips', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, title, destination, start_date, end_date, user_id, **kwargs):
        self.title = title
        self.destination = destination
        self.start_date = start_date
        self.end_date = end_date
        self.user_id = user_id
        
        self.latitude = kwargs.get('latitude')
        self.longitude = kwargs.get('longitude')
        self.description = kwargs.get('description', '')
        self.budget = kwargs.get('budget')
        self.status = kwargs.get('status', 'planned')
        
        itinerary_data = kwargs.get('itinerary')
        if itinerary_data:
            self.set_itinerary(itinerary_data)
    
    def set_itinerary(self, itinerary_data):
        if itinerary_data:
            self.itinerary = json.dumps(itinerary_data)
        else:
            self.itinerary = None
    
    def get_itinerary(self):
        if self.itinerary:
            try:
                return json.loads(self.itinerary)
            except json.JSONDecodeError:
                return []
        return []
    
    @staticmethod
    def validate_dates(start_date, end_date):
        if start_date >= end_date:
            return False, "End date must be after start date"
        
        if start_date < date.today():
            return False, "Start date cannot be in the past"
        
        if (end_date - start_date).days > 365:
            return False, "Trip cannot be longer than 1 year"
        
        return True, "Dates are valid"
    
    @staticmethod
    def validate_coordinates(latitude, longitude):
        if latitude is None and longitude is None:
            return True, "Coordinates are optional"
        
        if latitude is None or longitude is None:
            return False, "Both latitude and longitude must be provided"
        
        try:
            lat = float(latitude)
            lng = float(longitude)
            
            if not (-90 <= lat <= 90):
                return False, "Latitude must be between -90 and 90"
            
            if not (-180 <= lng <= 180):
                return False, "Longitude must be between -180 and 180"
            
            return True, "Coordinates are valid"
        except (ValueError, TypeError):
            return False, "Coordinates must be valid numbers"
    
    def get_duration_days(self):
        return (self.end_date - self.start_date).days + 1
    
    def is_active(self):
        today = date.today()
        return self.start_date <= today <= self.end_date and self.status == 'active'
    
    def is_upcoming(self):
        today = date.today()
        return self.start_date > today and self.status in ['planned', 'active']
    
    def is_past(self):
        today = date.today()
        return self.end_date < today
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'destination': self.destination,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'budget': float(self.budget) if self.budget else None,
            'status': self.status,
            'duration_days': self.get_duration_days(),
            'is_active': self.is_active(),
            'is_upcoming': self.is_upcoming(),
            'is_past': self.is_past(),
            'itinerary': self.get_itinerary(),
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Trip {self.title} to {self.destination}>'

    def generate_default_itinerary(self):
        """Generate default itinerary for this trip."""
        return ItineraryGenerator.generate_default_itinerary(
            start_date=self.start_date,
            end_date=self.end_date,
            destination=self.destination,
            description=self.description or "",
            title=self.title
        )
    
    def set_default_itinerary(self):
        """Set default itinerary if none exists."""
        if not self.itinerary:
            default_itinerary = self.generate_default_itinerary()
            self.set_itinerary(default_itinerary)
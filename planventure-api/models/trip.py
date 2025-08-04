from datetime import datetime
from . import db
import json

class Trip(db.Model):
    __tablename__ = 'trips'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Coordinates stored as separate latitude and longitude
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Itinerary stored as JSON text
    itinerary = db.Column(db.Text, nullable=True)
    
    # Additional trip details
    description = db.Column(db.Text, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='planned', nullable=False)  # planned, active, completed, cancelled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('trips', lazy=True, cascade='all, delete-orphan'))
    
    def __init__(self, title, destination, start_date, end_date, user_id, **kwargs):
        self.title = title
        self.destination = destination
        self.start_date = start_date
        self.end_date = end_date
        self.user_id = user_id
        
        # Optional fields
        self.latitude = kwargs.get('latitude')
        self.longitude = kwargs.get('longitude')
        self.description = kwargs.get('description')
        self.budget = kwargs.get('budget')
        self.status = kwargs.get('status', 'planned')
        
        # Handle itinerary
        itinerary_data = kwargs.get('itinerary')
        if itinerary_data:
            self.set_itinerary(itinerary_data)
    
    def set_coordinates(self, latitude, longitude):
        """Set trip coordinates."""
        self.latitude = float(latitude) if latitude is not None else None
        self.longitude = float(longitude) if longitude is not None else None
    
    def get_coordinates(self):
        """Get coordinates as a dictionary."""
        if self.latitude is not None and self.longitude is not None:
            return {
                'latitude': self.latitude,
                'longitude': self.longitude
            }
        return None
    
    def set_itinerary(self, itinerary_data):
        """Set itinerary from dictionary or list."""
        if isinstance(itinerary_data, (dict, list)):
            self.itinerary = json.dumps(itinerary_data)
        elif isinstance(itinerary_data, str):
            # Validate that it's valid JSON
            try:
                json.loads(itinerary_data)
                self.itinerary = itinerary_data
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format for itinerary")
        else:
            raise ValueError("Itinerary must be a dictionary, list, or valid JSON string")
    
    def get_itinerary(self):
        """Get itinerary as a Python object."""
        if self.itinerary:
            try:
                return json.loads(self.itinerary)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_duration_days(self):
        """Calculate trip duration in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @staticmethod
    def validate_dates(start_date, end_date):
        """Validate that end date is after start date."""
        if start_date >= end_date:
            return False, "End date must be after start date"
        return True, "Dates are valid"
    
    @staticmethod
    def validate_coordinates(latitude, longitude):
        """Validate latitude and longitude values."""
        try:
            lat = float(latitude) if latitude is not None else None
            lng = float(longitude) if longitude is not None else None
            
            if lat is not None and (lat < -90 or lat > 90):
                return False, "Latitude must be between -90 and 90"
            
            if lng is not None and (lng < -180 or lng > 180):
                return False, "Longitude must be between -180 and 180"
            
            return True, "Coordinates are valid"
        except (ValueError, TypeError):
            return False, "Coordinates must be valid numbers"
    
    def to_dict(self):
        """Convert trip object to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'destination': self.destination,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'coordinates': self.get_coordinates(),
            'itinerary': self.get_itinerary(),
            'description': self.description,
            'budget': self.budget,
            'status': self.status,
            'duration_days': self.get_duration_days(),
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Trip {self.title} to {self.destination}>'
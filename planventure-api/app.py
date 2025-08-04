from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Import models - this should come after the other imports
from models import db, User,Trip

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///planventure.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app, origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def home():
        return jsonify({"message": "Welcome to PlanVenture API"})
    
    @app.route('/health')
    def health_check():
        try:
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        
        return jsonify({
            "status": "healthy",
            "database": db_status,
            "users_count": User.query.count()
        })
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

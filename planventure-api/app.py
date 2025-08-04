from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from datetime import timedelta

# Import models
from models import db, User, Trip

# Import middleware
from middleware import AuthMiddleware, RequestMiddleware

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///planventure.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # JWT Configuration
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app, origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','))
    
    # Initialize middleware
    RequestMiddleware(app)
    
    # JWT Error Handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token required'}), 401
    
    # Register blueprints
    from routes import auth_bp, protected_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(protected_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def home():
        return jsonify({"message": "Welcome to PlanVenture API"})
    
    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = "connected"
            users_count = User.query.count()
            trips_count = Trip.query.count()
        except Exception:
            db_status = "disconnected"
            users_count = 0
            trips_count = 0
        
        return jsonify({
            "status": "healthy",
            "database": db_status,
            "users_count": users_count,
            "trips_count": trips_count
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

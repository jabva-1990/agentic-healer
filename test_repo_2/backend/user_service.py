from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import redis
from datetime import datetime, timedelta
import functools

app = Flask(__name__)
CORS(app)

# Configuration - SECURITY ISSUES
app.config['SECRET_KEY'] = 'dev_secret_key_123'  # Hardcoded secret
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'  # Another hardcoded secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Redis connection - NO ERROR HANDLING
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Missing __repr__ method
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # MISSING INPUT VALIDATION
    username = data['username']  # No .get() - will crash if missing
    email = data['email']
    password = data['password']
    
    # Check if user exists - INEFFICIENT QUERY
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
        
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Cache user info - POTENTIAL REDIS ERROR
        redis_client.setex(f'user:{user.id}', 3600, user.username)
        
        # User registration successful
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500  # No actual error details

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # MISSING NULL CHECKS
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400
    
    # Find user - SQL INJECTION VULNERABLE
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({'error': 'Account deactivated'}), 403
            
        # Create JWT token
        access_token = create_access_token(identity=user.id)
        
        # Update last login - MISSING ERROR HANDLING
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # User login successful
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    else:
        # Security issue: Different error messages reveal if username exists
        if user:
            return jsonify({'error': 'Invalid password'}), 401
        else:
            return jsonify({'error': 'User not found'}), 401

@app.route('/api/users/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    
    # Get from cache first - NO ERROR HANDLING
    cached_user = redis_client.get(f'user:{current_user_id}')
    if cached_user:
        # Cache hit for user profile
        pass
        
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat()
    })

@app.route('/api/users/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    
    # UNSAFE MASS ASSIGNMENT
    if 'username' in data:
        user.username = data['username']  # No uniqueness check
    if 'email' in data:
        user.email = data['email']  # No validation
        
    try:
        db.session.commit()
        
        # Update cache - POTENTIAL ERROR
        redis_client.setex(f'user:{user.id}', 3600, user.username)
        
        return jsonify({'message': 'Profile updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Update failed'}), 500

@app.route('/api/health')
def health_check():
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check Redis connection - NO TIMEOUT
        redis_client.ping()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'redis': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# MISSING ERROR HANDLERS
# @app.errorhandler(404)
# @app.errorhandler(500)

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()
        
    # INSECURE DEVELOPMENT SETTINGS
    # Starting User Service on port 3001
    app.run(host='0.0.0.0', port=3001, debug=True)  # Debug mode in production

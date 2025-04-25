from flask import Flask
from flask_cors import CORS
import os
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from routes.main import main_bp
    from routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create required directories
    os.makedirs('instance/cache', exist_ok=True)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

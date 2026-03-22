import os
from flask import Flask
from flask_cors import CORS
from .database import db
from .config import config_map


def create_app(env: str = 'development') -> Flask:
    config = config_map.get(env, config_map['default'])

    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates',
    )
    app.config.from_object(config)

    # Extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from .routes.main import main_bp
    from .routes.jobs import jobs_bp
    from .routes.candidates import candidates_bp
    from .routes.screening import screening_bp
    from .routes.dashboard import dashboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
    app.register_blueprint(candidates_bp, url_prefix='/api/candidates')
    app.register_blueprint(screening_bp, url_prefix='/api/screening')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # Create DB tables
    with app.app_context():
        db.create_all()

    return app

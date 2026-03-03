"""
Stripe Reconciliation Accelerator - Flask Web Application
Provides slug-based client isolation and automated reconciliation processing.
"""

import os
import logging
from io import BytesIO
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, abort, flash
from werkzeug.utils import secure_filename

from logic import StripeReconciliator

# authentication & database
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_wtf import CSRFProtect

from models import db, User
from auth import auth_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
# require secret key explicitly
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set.")
app.secret_key = secret_key

# security settings
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
# strict session cookie policies (secure flag may be overridden by the
# environment; e.g. set FLASK_ENV=production to enforce HTTPS cookies).
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ALLOWED_EXTENSIONS = {'csv'}

# initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)
csrf = CSRFProtect(app)

# register auth blueprint
app.register_blueprint(auth_bp)

# Store active reconciliators per client (in-memory)
active_reconciliators = {}

# TODO: Replace with database in production
VALID_CLIENTS = {
    'client_a': {'name': 'Client A', 'email': 'contact@clienta.com'},
    'client_b': {'name': 'Client B', 'email': 'contact@clientb.com'},
    'client_c': {'name': 'Client C', 'email': 'contact@clientc.com'},
    'demo': {'name': 'Demo Account', 'email': 'demo@striperecon.com'}
}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_client(f):
    """Decorator to validate the client slug exists in the client list.

    This helper does **not** perform authentication checks; it only
    verifies that the slug is known.  Routes needing a logged‑in user should
    also use `@login_required` and perform an additional check that
    ``current_user.client_slug`` matches the slug supplied in the URL.
    """
    @wraps(f)
    def decorated_function(client_slug, *args, **kwargs):
        if client_slug not in VALID_CLIENTS:
            logger.warning(f"Unauthorized access attempt for client: {client_slug}")
            return jsonify({'error': 'Invalid client'}), 403
        
        return f(client_slug, *args, **kwargs)
    return decorated_function


# --- login loader ----------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


def cleanup_old_reconciliators():
    """Clean up reconciliators that have been idle for too long."""
    current_time = datetime.now()
    clients_to_remove = []
    
    for client_slug, reconciliator_data in active_reconciliators.items():
        time_diff = (current_time - reconciliator_data.get('created_at', current_time)).total_seconds()
        # Clean up after 1 hour of inactivity
        if time_diff > 3600:
            clients_to_remove.append(client_slug)
    
    for client_slug in clients_to_remove:
        del active_reconciliators[client_slug]
        logger.info(f"Cleaned up old reconciliator for {client_slug}")


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page with client selection.

    If a user is already logged in we send them directly to their portal so
    they don't have to click twice.  Unauthenticated visitors will see the
    client list and be redirected to the login screen when they click a slug.
    """
    if current_user.is_authenticated:
        return redirect(url_for('client_portal', client_slug=current_user.client_slug))
    return render_template('index.html', clients=VALID_CLIENTS)


@app.route('/portal/<client_slug>', methods=['GET'])
@login_required
@validate_client
def client_portal(client_slug):
    """Main client portal - only the assigned user may enter."""
    if current_user.client_slug != client_slug:
        logger.warning(f"User {current_user.username} tried to access {client_slug}")
        abort(403)

    client_info = VALID_CLIENTS[client_slug]
    
    # Initialize reconciliator for this client
    if client_slug not in active_reconciliators:
        active_reconciliators[client_slug] = {
            'reconciliator': StripeReconciliator(),
            'created_at': datetime.now(),
            'status': 'ready'
        }
    
    logger.info(f"Client {client_slug} accessed portal")
    return render_template('portal.html', client_slug=client_slug, client_info=client_info)


@app.route('/api/portal/<client_slug>/upload', methods=['POST'])
@login_required
@validate_client
def upload_file(client_slug):
    """Handle file uploads for reconciliation.  Only the user assigned to the
    given ``client_slug`` may perform uploads.
    """
    if current_user.client_slug != client_slug:
        return jsonify({'error': 'Forbidden'}), 403
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type')
        
        if not file or not file_type:
            return jsonify({'error': 'Missing file or type'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        if file_type not in ['balance', 'payout', 'bank']:
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Get or create reconciliator
        cleanup_old_reconciliators()
        if client_slug not in active_reconciliators:
            active_reconciliators[client_slug] = {
                'reconciliator': StripeReconciliator(),
                'created_at': datetime.now(),
                'status': 'ready'
            }
        
        reconciliator = active_reconciliators[client_slug]['reconciliator']
        
        # Read file content (in-memory)
        file_content = file.read()
        
        # Load CSV
        success = reconciliator.load_csv(file_content, file_type)
        
        if success:
            logger.info(f"File uploaded for {client_slug}: {file_type}")
            return jsonify({
                'status': 'success',
                'message': f'{file_type.capitalize()} file uploaded successfully'
            }), 200
        else:
            # Get the error message from reconciliator exceptions
            error_msg = 'Failed to process file'
            if reconciliator.exceptions:
                error_msg = reconciliator.exceptions[-1]
            
            logger.error(f"File processing failed for {client_slug} ({file_type}): {error_msg}")
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400
    
    except Exception as e:
        logger.error(f"Error in upload for {client_slug}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Upload error: {str(e)}'}), 500


@app.route('/api/portal/<client_slug>/status', methods=['GET'])
@login_required
@validate_client
def get_status(client_slug):
    """Get reconciliation status for an authenticated user."""
    if current_user.client_slug != client_slug:
        return jsonify({'error': 'Forbidden'}), 403
    try:
        if client_slug not in active_reconciliators:
            return jsonify({
                'status': 'not-ready',
                'balance': False,
                'payout': False,
                'bank': False,
                'message': 'No files uploaded yet'
            }), 200
        
        reconciliator = active_reconciliators[client_slug]['reconciliator']
        
        return jsonify({
            'status': 'ready',
            'balance': reconciliator.balance_df is not None,
            'payout': reconciliator.payout_df is not None,
            'bank': reconciliator.bank_df is not None,
            'message': 'Ready to process' if all([
                reconciliator.balance_df is not None,
                reconciliator.payout_df is not None,
                reconciliator.bank_df is not None
            ]) else 'Waiting for files',
            'exceptions_count': len(reconciliator.exceptions)
        }), 200
    except Exception as e:
        logger.error(f"Error getting status for {client_slug}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portal/<client_slug>/process', methods=['POST'])
@login_required
@validate_client
def process_reconciliation(client_slug):
    """Process reconciliation and generate report for the authenticated user."""
    if current_user.client_slug != client_slug:
        return jsonify({'error': 'Forbidden'}), 403
    try:
        if client_slug not in active_reconciliators:
            return jsonify({'error': 'No files uploaded'}), 400
        
        reconciliator = active_reconciliators[client_slug]['reconciliator']
        
        # Validate all files are present
        if not all([reconciliator.balance_df is not None, 
                   reconciliator.payout_df is not None,
                   reconciliator.bank_df is not None]):
            return jsonify({'error': 'Not all required files have been uploaded'}), 400
        
        # read parameters from request JSON or form
        payload = request.get_json(silent=True) or request.form
        try:
            opening_bal = float(payload.get('opening_balance', 0.0))
        except Exception:
            opening_bal = 0.0
        try:
            tol = float(payload.get('tolerance', 5.0))
        except Exception:
            tol = 5.0
        
        logger.info(f"Processing reconciliation for {client_slug} with opening_balance={opening_bal} tolerance={tol}")
        
        # Process the files (reconciliation logic)
        success = reconciliator.process_files(opening_balance=opening_bal, tolerance=tol)
        
        if not success:
            error_msg = reconciliator.exceptions[-1] if reconciliator.exceptions else 'Processing failed'
            logger.error(f"Reconciliation processing failed: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        # Generate report
        report = reconciliator.generate_report()
        
        if report is None:
            error_msg = reconciliator.exceptions[-1] if reconciliator.exceptions else 'Failed to generate report'
            logger.error(f"Report generation failed: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        # Clean up reconciliator after successful processing
        del active_reconciliators[client_slug]
        
        logger.info(f"Report generated successfully for {client_slug}")
        
        return send_file(
            report,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'reconciliation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    
    except Exception as e:
        logger.error(f"Error processing reconciliation for {client_slug}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/portal/<client_slug>/reset', methods=['POST'])
@login_required
@validate_client
def reset_session(client_slug):
    """Reset reconciliation session for the logged in user."""
    if current_user.client_slug != client_slug:
        return jsonify({'error': 'Forbidden'}), 403
    try:
        if client_slug in active_reconciliators:
            del active_reconciliators[client_slug]
            logger.info(f"Session reset for {client_slug}")
        
        return jsonify({'status': 'success', 'message': 'Session reset'}), 200
    except Exception as e:
        logger.error(f"Error resetting session for {client_slug}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portal/<client_slug>/preview', methods=['GET'])
@login_required
@validate_client
def preview_data(client_slug):
    """Get preview of loaded data for the current user."""
    if current_user.client_slug != client_slug:
        return jsonify({'error': 'Forbidden'}), 403
    try:
        if client_slug not in active_reconciliators:
            return jsonify({'error': 'No data loaded'}), 400
        
        reconciliator = active_reconciliators[client_slug]['reconciliator']
        
        preview = {
            'balance_rows': len(reconciliator.balance_df) if reconciliator.balance_df is not None else 0,
            'payout_rows': len(reconciliator.payout_df) if reconciliator.payout_df is not None else 0,
            'bank_rows': len(reconciliator.bank_df) if reconciliator.bank_df is not None else 0,
            'exceptions': reconciliator.exceptions[:10],  # First 10 exceptions
            'total_exceptions': len(reconciliator.exceptions)
        }
        
        return jsonify(preview), 200
    except Exception as e:
        logger.error(f"Error getting preview for {client_slug}: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


@app.before_request
def before_request():
    """Cleanup old reconciliators before each request."""
    cleanup_old_reconciliators()


@app.after_request
def after_request(response):
    """Add security headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


# ==================== APPLICATION STARTUP ====================

# ensure database tables exist before first request
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Determine environment
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Stripe Reconciliation Accelerator (Port: {port})")
    # Debug flag omitted; use Gunicorn or set FLASK_ENV appropriately
    app.run(host='0.0.0.0', port=port)

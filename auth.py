from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from forms import LoginForm, RegisterForm


auth_bp = Blueprint('auth', __name__, template_folder='templates')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # already logged in, send to own portal
        return redirect(url_for('client_portal', client_slug=current_user.client_slug))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully', 'success')
            next_page = request.args.get('next')
            # security: ensure next_page is safe
            if next_page:
                return redirect(next_page)
            return redirect(url_for('client_portal', client_slug=user.client_slug))
        flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # only admin users may create other accounts
    if not current_user.is_admin:
        return "Forbidden", 403

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing:
            flash('User already exists', 'error')
        else:
            user = User(
                username=form.username.data,
                client_slug=form.client_slug.data,
                is_admin=form.is_admin.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.username} created', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

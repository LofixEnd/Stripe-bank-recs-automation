"""Utility script to create a new user in the SQLite database.

Run this after setting the `DATABASE_URL` (or rely on default) and exporting
`SECRET_KEY` so that the Flask app can initialize correctly.

Example usage:

    python create_user.py

The script will prompt for username, password, client slug and whether the user
should be an administrator.  The database tables are created if they do not
exist.
"""
import getpass
import os

from app import app
from models import db, User


def prompt_bool(prompt):
    val = input(prompt + ' [y/N]: ').strip().lower()
    return val in ('y', 'yes')


def main():
    with app.app_context():
        db.create_all()

        username = input('Username: ').strip()
        if not username:
            print('Username is required')
            return

        if User.query.filter_by(username=username).first():
            print('User already exists')
            return

        password = getpass.getpass('Password: ')
        confirm = getpass.getpass('Confirm password: ')
        if password != confirm or not password:
            print('Passwords do not match or are empty')
            return

        client_slug = input('Client slug: ').strip()
        if not client_slug:
            print('Client slug is required')
            return

        is_admin = prompt_bool('Grant admin privileges?')

        user = User(username=username, client_slug=client_slug, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Created user {username} (admin={is_admin}) for client {client_slug}')


if __name__ == '__main__':
    main()

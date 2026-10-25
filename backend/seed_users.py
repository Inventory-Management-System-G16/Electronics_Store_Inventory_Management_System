
"""Create demo users for local development only."""
import secrets

from werkzeug.security import generate_password_hash
from app import app, execute

users = [
    ("admin_demo", "admin@example.test", "admin"),
    ("manager_demo", "manager@example.test", "store_manager"),
    ("employee_demo", "employee@example.test", "store_employee"),
    ("management_demo", "management@example.test", "management"),
]

with app.app_context():
    for username, email, role in users:
        exists = execute(
            "SELECT user_id FROM users WHERE username = %s",
            (username,),
            fetchone=True,
        )

        if not exists:
            password = secrets.token_urlsafe(12)

            execute(
                """INSERT INTO users
                   (username, email, password_hash, role, is_active)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    username,
                    email,
                    generate_password_hash(password),
                    role,
                    True,
                ),
                commit=True,
            )

            print(
                f"Created {username} ({role}) "
                f"with one-time password: {password}"
            )
        else:
            print(f"Skipped {username}; it already exists.")

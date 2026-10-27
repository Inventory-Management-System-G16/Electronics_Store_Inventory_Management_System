"""Create or reset demo users for local development only."""

from werkzeug.security import generate_password_hash
from app import app, execute


users = [
    ("admin_demo", "admin@example.test", "AdminDemo@123", "admin"),
    ("manager_demo", "manager@example.test", "ManagerDemo@123", "store_manager"),
    ("employee_demo", "employee@example.test", "EmployeeDemo@123", "store_employee"),
    ("management_demo", "management@example.test", "ManagementDemo@123", "management"),
]


with app.app_context():
    for username, email, password, role in users:

        existing = execute(
            "SELECT user_id FROM users WHERE username = %s",
            (username,),
            fetchone=True,
        )

        password_hash = generate_password_hash(password)

        if existing:
            execute(
                """
                UPDATE users
                SET password_hash = %s,
                    email = %s,
                    role = %s,
                    is_active = %s
                WHERE username = %s
                """,
                (password_hash, email, role, True, username),
                commit=True,
            )
            print(f"Password reset for {username}: {password}")

        else:
            execute(
                """
                INSERT INTO users
                    (username, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (username, email, password_hash, role, True),
                commit=True,
            )
            print(f"Created {username}: {password}")

print("Demo-user setup completed.")
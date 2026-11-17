"""Check that the app can reach the database from your .env file.

Run from the backend folder:   python check_db_connection.py
It prints the tables it finds. It never prints your password.
"""
from app import app, execute


def main():
    with app.app_context():
        tables = execute("SHOW TABLES", fetchall=True)
        print("Connected. Tables found:")
        for row in tables:
            print("  -", list(row.values())[0] if isinstance(row, dict) else row[0])
        users = execute("SELECT COUNT(*) AS n FROM users", fetchone=True)
        products = execute("SELECT COUNT(*) AS n FROM products", fetchone=True)
        print("users:", users["n"] if isinstance(users, dict) else users[0])
        print("products:", products["n"] if isinstance(products, dict) else products[0])


if __name__ == "__main__":
    main()

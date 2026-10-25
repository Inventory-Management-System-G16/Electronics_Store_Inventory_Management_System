"""ESIMS Flask application: Sprint 1 authentication, RBAC and add-product features.

This application is intentionally modular so its blueprints can be registered in the
team's inventory application during integration.
"""
import os
import sqlite3
from decimal import Decimal
from functools import wraps

from flask import Flask, abort, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

ROLES = {"admin", "store_manager", "store_employee", "management"}


def get_db():
    """Return a request-scoped DB connection. SQLite is used for local tests; MySQL in normal use."""
    if "db" not in g:
        if g.get("_test_db"):
            g.db = g._test_db
        elif current_app.config.get("DB_DRIVER", os.environ.get("DB_DRIVER", "mysql")).lower() == "sqlite":
            path = current_app.config.get("SQLITE_PATH", os.environ.get("SQLITE_PATH", "esims.db"))
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            g.db = conn
        else:
            import mysql.connector
            g.db = mysql.connector.connect(
                host=os.environ.get("DB_HOST", "localhost"),
                port=int(os.environ.get("DB_PORT", "3306")),
                user=os.environ.get("DB_USER", "root"),
                password=os.environ.get("DB_PASSWORD", ""),
                database=os.environ.get("DB_NAME", "esims_db"),
            )
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def execute(sql, params=(), *, fetchone=False, fetchall=False, commit=False):
    """Small DB adapter for MySQL (%s) and SQLite (?) parameter placeholders."""
    db = get_db()
    is_sqlite = isinstance(db, sqlite3.Connection)
    if is_sqlite:
        sql = sql.replace("%s", "?")
        cur = db.cursor()
        cur.execute(sql, params)
    else:
        cur = db.cursor(dictionary=True)
        cur.execute(sql, params)
    result = cur.fetchone() if fetchone else cur.fetchall() if fetchall else None
    if commit:
        db.commit()
    cur.close()
    return result


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                if request.path.startswith("/api/"):
                    abort(401)
                return redirect(url_for("login", next=request.path))
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DB_DRIVER=os.environ.get("DB_DRIVER", "mysql"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=1800,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        if app.config.get("TESTING"):
            app.config["SECRET_KEY"] = "test-only-secret-not-for-production"
        else:
            raise RuntimeError("Set a strong SECRET_KEY environment variable before starting Flask.")

    app.teardown_appcontext(close_db)

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.get("/")
    def home():
        if session.get("user_id"):
            return redirect(url_for("inventory"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            return render_template("login.html", error="Enter your username/email and password."), 400
        user = execute(
            "SELECT user_id, username, email, password_hash, role, is_active FROM users WHERE username = %s OR email = %s LIMIT 1",
            (username, username), fetchone=True,
        )
        # SQLite Row and MySQL dictionary cursors both support key lookup.
        if not user or not user["is_active"] or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid username/email or password."), 401
        session.clear()
        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session.permanent = True
        target = request.args.get("next", "")
        # Avoid open redirects: only accept local absolute paths.
        if not target.startswith("/") or target.startswith("//"):
            target = url_for("inventory")
        return redirect(target)

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.get("/inventory")
    @login_required
    def inventory():
        search = request.args.get("search", "").strip()
        search_by = request.args.get("search_by", "product_id")
        allowed_columns = {"product_id": "product_id", "product_name": "product_name", "category": "category"}
        column = allowed_columns.get(search_by, "product_id")
        if search:
            products = execute(
                f"SELECT product_id, product_name, category, price, quantity, reorder_level, location FROM products WHERE {column} LIKE %s ORDER BY product_id",
                (f"%{search}%",), fetchall=True,
            )
        else:
            products = execute("SELECT product_id, product_name, category, price, quantity, reorder_level, location FROM products ORDER BY product_id", fetchall=True)
        return render_template("inventory.html", products=products, search=search, search_by=search_by)

    @app.route("/add-product", methods=["GET", "POST"])
    @roles_required("admin", "store_manager")
    def add_product():
        if request.method == "GET":
            return render_template("add_product.html")
        values = {
            "product_id": request.form.get("product_id", "").strip(),
            "product_name": request.form.get("product_name", "").strip(),
            "category": request.form.get("category", "").strip(),
            "price": request.form.get("price", "").strip(),
            "quantity": request.form.get("quantity", "").strip(),
            "reorder_level": request.form.get("reorder_level", "").strip(),
            "location": request.form.get("location", "").strip(),
        }
        error = validate_product(values)
        if error:
            return render_template("add_product.html", values=values, error=error), 400
        existing = execute("SELECT product_id FROM products WHERE product_id = %s", (values["product_id"],), fetchone=True)
        if existing:
            return render_template("add_product.html", values=values, error="Product ID already exists."), 409
        try:
            execute(
                "INSERT INTO products (product_id, product_name, category, price, quantity, reorder_level, location) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (values["product_id"], values["product_name"], values["category"], str(Decimal(values["price"])), int(values["quantity"]), int(values["reorder_level"]), values["location"] or None),
                commit=True,
            )
        except Exception as exc:
            # Handle duplicate races without leaking SQL/credentials to the user.
            if "duplicate" in str(exc).lower() or "unique" in str(exc).lower() or "integrity" in str(exc).lower():
                return render_template("add_product.html", values=values, error="Product ID already exists."), 409
            app.logger.exception("Database error while adding product")
            return render_template("add_product.html", values=values, error="Could not save the product. Please try again."), 500
        flash("Product added successfully.", "success")
        return redirect(url_for("inventory"))

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("403.html"), 403

    return app


def validate_product(values):
    """Return a user-safe validation message, or None if fields are valid."""
    required = ("product_id", "product_name", "category", "price", "quantity", "reorder_level")
    if any(not values.get(field) for field in required):
        return "Please fill in all required fields."
    limits = {"product_id": 30, "product_name": 100, "category": 50, "location": 50}
    for field, maximum in limits.items():
        if len(values.get(field, "")) > maximum:
            return f"{field.replace('_', ' ').capitalize()} must be at most {maximum} characters."
    try:
        price = Decimal(values["price"])
        quantity = int(values["quantity"])
        reorder = int(values["reorder_level"])
    except (ValueError, ArithmeticError):
        return "Price must be a decimal and quantity/reorder level must be whole numbers."
    if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
        return "Price must be non-negative and have at most two decimal places."
    if quantity < 0 or reorder < 0:
        return "Quantity and reorder level cannot be negative."
    # Reject decimal-like integer strings such as 2.5 (int already rejects them).
    return None


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")

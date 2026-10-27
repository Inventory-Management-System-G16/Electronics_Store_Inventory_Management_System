"""
Electronics Store Inventory Management System (ESIMS)
Flask application: Authentication, inventory, product management,
role-based access control, and dashboard.
"""

import os
import sqlite3
from pathlib import Path
from decimal import Decimal
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

ROLES = {
    "admin",
    "store_manager",
    "store_employee",
    "management",
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    """Return a database connection for the current request."""

    if "db" not in g:

        if g.get("_test_db"):
            g.db = g._test_db

        elif (
            current_app.config.get(
                "DB_DRIVER",
                os.environ.get("DB_DRIVER", "mysql"),
            ).lower()
            == "sqlite"
        ):
            database_path = current_app.config.get(
                "SQLITE_PATH",
                os.environ.get("SQLITE_PATH", "esims.db"),
            )

            connection = sqlite3.connect(database_path)
            connection.row_factory = sqlite3.Row
            g.db = connection

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
    """Close the current request's database connection."""

    database = g.pop("db", None)

    if database is not None:
        database.close()


def execute(
    sql,
    params=(),
    *,
    fetchone=False,
    fetchall=False,
    commit=False,
):
    """Execute a parameterized SQL query for MySQL or SQLite."""

    database = get_db()

    is_sqlite = isinstance(database, sqlite3.Connection)

    if is_sqlite:
        sql = sql.replace("%s", "?")
        cursor = database.cursor()
        cursor.execute(sql, params)

    else:
        cursor = database.cursor(dictionary=True)
        cursor.execute(sql, params)

    if fetchone:
        result = cursor.fetchone()

    elif fetchall:
        result = cursor.fetchall()

    else:
        result = None

    if commit:
        database.commit()

    cursor.close()

    return result


# ============================================================
# AUTHENTICATION AND ROLE PERMISSIONS
# ============================================================

def login_required(view):
    """Require the user to be logged in."""

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("user_id"):
            flash("Please log in to continue.", "error")

            return redirect(
                url_for("login", next=request.path)
            )

        return view(*args, **kwargs)

    return wrapped


def roles_required(*roles):
    """Restrict a route to specified user roles."""

    def decorator(view):

        @wraps(view)
        def wrapped(*args, **kwargs):

            if not session.get("user_id"):

                if request.path.startswith("/api/"):
                    abort(401)

                return redirect(
                    url_for("login", next=request.path)
                )

            if session.get("role") not in roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator


# ============================================================
# CREATE FLASK APPLICATION
# ============================================================

def create_app(test_config=None):

    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DB_DRIVER=os.environ.get("DB_DRIVER", "mysql"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(
            os.environ.get("COOKIE_SECURE", "0") == "1"
        ),
        PERMANENT_SESSION_LIFETIME=1800,
    )

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):

        if app.config.get("TESTING"):
            app.config["SECRET_KEY"] = (
                "test-only-secret-not-for-production"
            )

        else:
            raise RuntimeError(
                "Set a strong SECRET_KEY environment variable "
                "before starting Flask."
            )

    app.teardown_appcontext(close_db)

    # --------------------------------------------------------
    # SECURITY HEADERS
    # --------------------------------------------------------

    @app.after_request
    def security_headers(response):

        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )

        response.headers.setdefault(
            "X-Frame-Options",
            "DENY",
        )

        response.headers.setdefault(
            "Cache-Control",
            "no-store",
        )

        return response

    # --------------------------------------------------------
    # HOME PAGE
    # --------------------------------------------------------

    @app.get("/")
    def home():

        if session.get("user_id"):
            return redirect(url_for("dashboard"))

        return redirect(url_for("login"))

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    @app.route("/login", methods=["GET", "POST"])
    def login():

        if request.method == "GET":
            return render_template("login.html")

        username = request.form.get(
            "username",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        if not username or not password:

            return render_template(
                "login.html",
                error="Enter your username/email and password.",
            ), 400

        user = execute(
            """
            SELECT
                user_id,
                username,
                email,
                password_hash,
                role,
                is_active
            FROM users
            WHERE username = %s OR email = %s
            LIMIT 1
            """,
            (username, username),
            fetchone=True,
        )

        if (
            not user
            or not user["is_active"]
            or not check_password_hash(
                user["password_hash"],
                password,
            )
        ):

            return render_template(
                "login.html",
                error="Invalid username/email or password.",
            ), 401

        session.clear()

        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session.permanent = True

        target = request.args.get("next", "")

        if not target.startswith("/") or target.startswith("//"):
            target = url_for("dashboard")

        return redirect(target)

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

    @app.post("/logout")
    @login_required
    def logout():

        session.clear()

        flash(
            "You have been logged out.",
            "success",
        )

        return redirect(url_for("login"))

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    @app.get("/dashboard")
    @login_required
    def dashboard():

        total_products = execute(
            """
            SELECT COUNT(*) AS total
            FROM products
            """,
            fetchone=True,
        )["total"]

        total_stock = execute(
            """
            SELECT COALESCE(SUM(quantity), 0) AS total
            FROM products
            """,
            fetchone=True,
        )["total"]

        low_stock = execute(
            """
            SELECT COUNT(*) AS total
            FROM products
            WHERE quantity > 0
              AND quantity <= reorder_level
            """,
            fetchone=True,
        )["total"]

        out_of_stock = execute(
            """
            SELECT COUNT(*) AS total
            FROM products
            WHERE quantity = 0
            """,
            fetchone=True,
        )["total"]

        return render_template(
            "dashboard.html",
            total_products=total_products,
            total_stock=total_stock,
            low_stock=low_stock,
            out_of_stock=out_of_stock,
        )

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    @app.get("/inventory")
    @login_required
    def inventory():

        search = request.args.get(
            "search",
            "",
        ).strip()

        search_by = request.args.get(
            "search_by",
            "product_id",
        )

        allowed_columns = {
            "product_id": "product_id",
            "product_name": "product_name",
            "category": "category",
        }

        column = allowed_columns.get(
            search_by,
            "product_id",
        )

        if search:

            products = execute(
                f"""
                SELECT
                    product_id,
                    product_name,
                    category,
                    price,
                    quantity,
                    reorder_level,
                    location
                FROM products
                WHERE {column} LIKE %s
                ORDER BY product_id
                """,
                (f"%{search}%",),
                fetchall=True,
            )

        else:

            products = execute(
                """
                SELECT
                    product_id,
                    product_name,
                    category,
                    price,
                    quantity,
                    reorder_level,
                    location
                FROM products
                ORDER BY product_id
                """,
                fetchall=True,
            )

        return render_template(
            "inventory.html",
            products=products,
            search=search,
            search_by=search_by,
        )

    # --------------------------------------------------------
    # ADD PRODUCT
    # --------------------------------------------------------

    @app.route("/add-product", methods=["GET", "POST"])
    @roles_required("admin", "store_manager")
    def add_product():

        if request.method == "GET":
            return render_template("add_product.html")

        values = {
            "product_id": request.form.get(
                "product_id", ""
            ).strip(),

            "product_name": request.form.get(
                "product_name", ""
            ).strip(),

            "category": request.form.get(
                "category", ""
            ).strip(),

            "price": request.form.get(
                "price", ""
            ).strip(),

            "quantity": request.form.get(
                "quantity", ""
            ).strip(),

            "reorder_level": request.form.get(
                "reorder_level", ""
            ).strip(),

            "location": request.form.get(
                "location", ""
            ).strip(),
        }

        error = validate_product(values)

        if error:

            return render_template(
                "add_product.html",
                values=values,
                error=error,
            ), 400

        existing = execute(
            """
            SELECT product_id
            FROM products
            WHERE product_id = %s
            """,
            (values["product_id"],),
            fetchone=True,
        )

        if existing:

            return render_template(
                "add_product.html",
                values=values,
                error="Product ID already exists.",
            ), 409

        try:

            execute(
                """
                INSERT INTO products (
                    product_id,
                    product_name,
                    category,
                    price,
                    quantity,
                    reorder_level,
                    location
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    values["product_id"],
                    values["product_name"],
                    values["category"],
                    str(Decimal(values["price"])),
                    int(values["quantity"]),
                    int(values["reorder_level"]),
                    values["location"] or None,
                ),
                commit=True,
            )

        except Exception as exc:

            message = str(exc).lower()

            if (
                "duplicate" in message
                or "unique" in message
                or "integrity" in message
            ):

                return render_template(
                    "add_product.html",
                    values=values,
                    error="Product ID already exists.",
                ), 409

            app.logger.exception(
                "Database error while adding product"
            )

            return render_template(
                "add_product.html",
                values=values,
                error="Could not save the product. Please try again.",
            ), 500

        flash(
            "Product added successfully.",
            "success",
        )

        return redirect(url_for("inventory"))

    # --------------------------------------------------------
    # FORBIDDEN PAGE
    # --------------------------------------------------------

    @app.errorhandler(403)
    def forbidden(_error):

        return render_template("403.html"), 403

    return app


# ============================================================
# PRODUCT VALIDATION
# ============================================================

def validate_product(values):

    required = (
        "product_id",
        "product_name",
        "category",
        "price",
        "quantity",
        "reorder_level",
    )

    if any(not values.get(field) for field in required):

        return "Please fill in all required fields."

    limits = {
        "product_id": 30,
        "product_name": 100,
        "category": 50,
        "location": 50,
    }

    for field, maximum in limits.items():

        if len(values.get(field, "")) > maximum:

            return (
                f"{field.replace('_', ' ').capitalize()} "
                f"must be at most {maximum} characters."
            )

    try:

        price = Decimal(values["price"])
        quantity = int(values["quantity"])
        reorder = int(values["reorder_level"])

    except (ValueError, ArithmeticError):

        return (
            "Price must be a decimal and quantity/reorder "
            "level must be whole numbers."
        )

    if (
        not price.is_finite()
        or price < 0
        or price.as_tuple().exponent < -2
    ):

        return (
            "Price must be non-negative and have "
            "at most two decimal places."
        )

    if quantity < 0 or reorder < 0:

        return "Quantity and reorder level cannot be negative."

    return None


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

app = create_app()

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
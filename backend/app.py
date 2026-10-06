from flask import Flask, render_template , request
import mysql.connector

app = Flask(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Shreyas@2006",
        database="esims_db"
    )


@app.route("/")
def home():
    return "Electronics Store Inventory Management System"


@app.route("/test-db")
def test_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return f"Database connected. Products: {count}"


@app.route("/inventory")
def inventory():
    search = request.args.get("search", "")
    search_by = request.args.get("search_by", "product_id")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if search:
        if search_by == "product_id":
            query = """
                SELECT
                    product_id,
                    product_name,
                    category,
                    price,
                    quantity,
                    reorder_level,
                    location
                FROM products
                WHERE product_id LIKE %s
                ORDER BY product_id
            """
        elif search_by == "product_name":
            query = """
                SELECT
                    product_id,
                    product_name,
                    category,
                    price,
                    quantity,
                    reorder_level,
                    location
                FROM products
                WHERE product_name LIKE %s
                ORDER BY product_id
            """
        else:
            query = """
                SELECT
                    product_id,
                    product_name,
                    category,
                    price,
                    quantity,
                    reorder_level,
                    location
                FROM products
                WHERE category LIKE %s
                ORDER BY product_id
            """

        cursor.execute(query, (f"%{search}%",))

    else:
        cursor.execute("""
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
        """)

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "inventory.html",
        products=products,
        search=search,
        search_by=search_by
    )


if __name__ == "__main__":
    app.run(debug=True)
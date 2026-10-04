from flask import Flask, render_template
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
    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

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

    return render_template("inventory.html", products=products)


if __name__ == "__main__":
    app.run(debug=True)
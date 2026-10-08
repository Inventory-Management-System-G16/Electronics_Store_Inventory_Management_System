from flask import Flask, render_template, request, redirect, url_for
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


# --------------------------------------------------
# VIEW + SEARCH INVENTORY
# --------------------------------------------------

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


# --------------------------------------------------
# UPDATE PRODUCT
# --------------------------------------------------

@app.route("/update-product/<product_id>", methods=["GET", "POST"])
def update_product(product_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        product_name = request.form["product_name"].strip()
        category = request.form["category"].strip()
        price = request.form["price"]
        quantity = request.form["quantity"]
        reorder_level = request.form["reorder_level"]
        location = request.form["location"].strip()

        # Validate numeric values
        try:
            price_value = float(price)
            quantity_value = int(quantity)
            reorder_level_value = int(reorder_level)

        except ValueError:
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
                WHERE product_id = %s
            """, (product_id,))

            product = cursor.fetchone()

            cursor.close()
            connection.close()

            return render_template(
                "update_product.html",
                product=product,
                error="Please enter valid numeric values."
            )

        # Reject negative values
        if price_value < 0 or quantity_value < 0 or reorder_level_value < 0:

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
                WHERE product_id = %s
            """, (product_id,))

            product = cursor.fetchone()

            cursor.close()
            connection.close()

            return render_template(
                "update_product.html",
                product=product,
                error="Price, quantity, and reorder level cannot be negative."
            )

        # Update product
        cursor.execute("""
            UPDATE products
            SET
                product_name = %s,
                category = %s,
                price = %s,
                quantity = %s,
                reorder_level = %s,
                location = %s
            WHERE product_id = %s
        """, (
            product_name,
            category,
            price_value,
            quantity_value,
            reorder_level_value,
            location,
            product_id
        ))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("inventory"))

    # Get existing product
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
        WHERE product_id = %s
    """, (product_id,))

    product = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "update_product.html",
        product=product
    )


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
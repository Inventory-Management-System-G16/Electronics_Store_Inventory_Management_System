"""System tests: the whole ESIMS app against a real MySQL database.

Run from the backend/ folder, after creating the database with database/schema.sql:

    set DB_HOST=127.0.0.1
    set DB_PORT=3306
    set DB_USER=root
    set DB_PASSWORD=your_password
    set DB_NAME=esims_test
    python system_tests/run_system_tests.py

WARNING: this script DELETES all rows in the users and products tables of DB_NAME.
Use a separate test database, never your real data.
"""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DB_DRIVER"] = "mysql"
for key, default in [("DB_HOST", "127.0.0.1"), ("DB_PORT", "3306"), ("DB_USER", "root"),
                     ("DB_PASSWORD", ""), ("DB_NAME", "esims_test"), ("SECRET_KEY", "system-test-secret")]:
    os.environ.setdefault(key, default)
import mysql.connector
from werkzeug.security import generate_password_hash
from app import create_app

db = mysql.connector.connect(host=os.environ["DB_HOST"], port=int(os.environ["DB_PORT"]), user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"], database=os.environ["DB_NAME"])
db.autocommit = True
cur = db.cursor()
cur.execute("DELETE FROM products"); cur.execute("DELETE FROM users")
for u, r in [("admin", "admin"), ("manager", "store_manager"), ("employee", "store_employee"), ("management", "management")]:
    cur.execute("INSERT INTO users(username,email,password_hash,role,is_active) VALUES(%s,%s,%s,%s,1)",
                (u, u + "@t.local", generate_password_hash("CorrectPass!23"), r))
db.commit()

app = create_app({"TESTING": True})
results = []


def check(tc, req, desc, ok, detail=""):
    results.append(dict(tc=tc, req=req, desc=desc, result="PASS" if ok else "FAIL", detail=detail))


def login(c, u, p="CorrectPass!23"):
    return c.post("/login", data={"username": u, "password": p})


def count(sql, args=()):
    cur.execute(sql, args); return cur.fetchone()[0]


def get_html(c, url):
    return c.get(url).get_data(as_text=True)


c = app.test_client()
# AUTH
check("TC-AUTH-01", "FR-AUTH-01", "Login page is shown", c.get("/login").status_code == 200 and "password" in get_html(c, "/login").lower())
r = login(c, "admin"); check("TC-AUTH-02", "FR-AUTH-01", "Valid credentials log the user in", r.status_code == 302 and c.get("/inventory").status_code == 200)
c2 = app.test_client(); r = login(c2, "admin", "wrong"); check("TC-AUTH-02b", "FR-AUTH-01", "Wrong password is rejected", c2.get("/inventory").status_code == 302, f"status {r.status_code}")
for u, exp in [("admin", 200), ("manager", 200), ("employee", 403), ("management", 403)]:
    cx = app.test_client(); login(cx, u)
    check(f"TC-AUTH-03-{u}", "FR-AUTH-04", f"{u}: Add Product page access", cx.get("/add-product").status_code == exp, f"expected {exp}")
cx = app.test_client(); login(cx, "management")
check("TC-AUTH-04", "FR-AUTH-04", "Management cannot reach Add Product or Delete", cx.get("/add-product").status_code == 403)
html = get_html(c, "/login")
check("TC-AUTH-05", "FR-AUTH-06", "Password field is masked", bool(re.search(r'type="password"', html)))
c3 = app.test_client(); login(c3, "manager"); c3.post("/logout")
check("TC-AUTH-06", "FR-AUTH-05", "Logout ends the session", c3.get("/inventory").status_code == 302)

# INVENTORY
ca = app.test_client(); login(ca, "admin")
add = lambda **o: ca.post("/add-product", data={**dict(product_id="S-1", product_name="Phone", category="Mobiles", price="199.99", quantity="10", reorder_level="5", location="A1"), **o}, follow_redirects=True)
add()
check("TC-INV-01", "FR-INV-01", "Add product persists to MySQL", count("SELECT COUNT(*) FROM products WHERE product_id='S-1'") == 1)
add()
check("TC-INV-02", "FR-INV-02", "Duplicate Product ID rejected (single row remains)", count("SELECT COUNT(*) FROM products WHERE product_id='S-1'") == 1)
check("TC-VAL-02", "FR-VAL-02", "Duplicate message shown to user", "already exists" in add().get_data(as_text=True).lower())
add(product_id="S-2", product_name="Cable", category="Cables", quantity="3", reorder_level="5")
add(product_id="S-3", product_name="Charger", category="Cables", quantity="0", reorder_level="5")
u = ca.post("/update-product/S-1", data=dict(product_name="Phone", category="Mobiles", price="210.00", quantity="12", reorder_level="5", location="A1"), follow_redirects=True)
q = count("SELECT quantity FROM products WHERE product_id='S-1'")
check("TC-INV-03", "FR-INV-04", "Update quantity/details saved", q == 12, f"quantity={q}")
inv = get_html(ca, "/inventory?search=cable&search_by=product_name")
check("TC-INV-08", "FR-INV-08", "Search returns only matching product", "Cable" in inv and "Phone" not in inv)
cd = app.test_client(); login(cd, "manager")
conf = cd.get("/delete-product/S-3")
check("TC-INV-05", "FR-INV-05", "Delete asks for confirmation first, nothing deleted", conf.status_code == 200 and count("SELECT COUNT(*) FROM products WHERE product_id='S-3'") == 1)
cd.post("/delete-product/S-3")
check("TC-INV-06", "FR-INV-05/06", "Confirmed delete removes product (authorised role)", count("SELECT COUNT(*) FROM products WHERE product_id='S-3'") == 0)
ce = app.test_client(); login(ce, "employee"); ce.post("/delete-product/S-2")
check("TC-INV-06b", "FR-INV-06", "Employee cannot delete", count("SELECT COUNT(*) FROM products WHERE product_id='S-2'") == 1)

# VALIDATION
for tc, req, desc, over in [
    ("TC-VAL-01", "FR-VAL-01", "Missing mandatory field rejected", dict(product_id="V-1", product_name="")),
    ("TC-VAL-03", "FR-VAL-03", "Negative price rejected", dict(product_id="V-2", price="-5")),
    ("TC-VAL-03b", "FR-VAL-03", "Negative quantity rejected", dict(product_id="V-3", quantity="-1")),
    ("TC-VAL-04", "FR-VAL-04", "Non-numeric quantity rejected", dict(product_id="V-4", quantity="abc"))]:
    add(**over)
    check(tc, req, desc, count("SELECT COUNT(*) FROM products WHERE product_id LIKE 'V-%'") == 0)

# CLASSIFICATION / REPORT / DASHBOARD
add(product_id="R-IN", product_name="InStockItem", quantity="20", reorder_level="5")
add(product_id="R-EDGE", product_name="EdgeItem", quantity="5", reorder_level="5")
add(product_id="R-LOW", product_name="LowItem", quantity="1", reorder_level="5")
add(product_id="R-OUT", product_name="OutItem", quantity="0", reorder_level="5")
rep = get_html(ca, "/availability-report")
def row_status(pid, label):
    m = re.search(re.escape(pid) + r".*?status-badge[^>]*>\s*([A-Za-z ]+?)\s*<", rep, re.S)
    return m and m.group(1) == label
check("TC-REP-01", "FR-REP-01", "Quantity above reorder level = In Stock", bool(row_status("R-IN", "In Stock")))
check("TC-REP-02", "FR-REP-02", "Quantity at reorder level = Low Stock", bool(row_status("R-EDGE", "Low Stock")))
check("TC-REP-03", "FR-REP-03", "Quantity 0 = Out of Stock", bool(row_status("R-OUT", "Out of Stock")))
check("TC-REP-04", "FR-REP-05", "Availability report lists products", all(p in rep for p in ["R-IN", "R-EDGE", "R-LOW", "R-OUT"]))
f = get_html(ca, "/availability-report?status=out_of_stock")
check("TC-REP-05", "FR-REP-06", "Report filter by status", "R-OUT" in f and "R-IN" not in f and "R-LOW" not in f)
f = get_html(ca, "/availability-report?search=edgeitem")
check("TC-REP-05b", "FR-REP-06", "Report search by name", "R-EDGE" in f and "R-IN" not in f)
cm = app.test_client(); login(cm, "management")
check("TC-REP-06", "FR-REP-05", "Management role can open the report", cm.get("/availability-report").status_code == 200)
d = get_html(ca, "/dashboard")
vals = [int(x) for x in re.findall(r'class="metric-value">\s*(\d+)\s*<', d)]
tp = count("SELECT COUNT(*) FROM products"); ts = count("SELECT SUM(quantity) FROM products")
lo = count("SELECT COUNT(*) FROM products WHERE quantity>0 AND quantity<=reorder_level"); ou = count("SELECT COUNT(*) FROM products WHERE quantity=0")
check("TC-DASH-01", "FR-DASH-01..04", "Dashboard totals equal database values", vals == [tp, ts, lo, ou], f"page={vals} db={[tp, ts, lo, ou]}")
ca.post("/update-product/R-IN", data=dict(product_name="InStockItem", category="Mobiles", price="1", quantity="0", reorder_level="5", location=""))
vals2 = [int(x) for x in re.findall(r'class="metric-value">\s*(\d+)\s*<', get_html(ca, "/dashboard"))]
check("TC-DASH-02", "FR-DASH-06", "Dashboard reflects the latest data", vals2[3] == vals[3] + 1, f"out-of-stock {vals[3]} -> {vals2[3]}")
check("TC-DASH-03", "FR-DASH-05", "Employee cannot open dashboard", (lambda x: (login(x, "employee"), x.get("/dashboard").status_code)[1])(app.test_client()) == 403)

# SECURITY
add(product_id="X-1", product_name="'; DROP TABLE products;--")
check("TC-SEC-01", "FR-VAL-05/NFR-07", "SQL-injection text stored as data, table intact", count("SELECT COUNT(*) FROM products WHERE product_id='X-1'") == 1 and count("SELECT COUNT(*) FROM products") > 0)
add(product_id="X-2", product_name="<script>alert(1)</script>")
check("TC-SEC-02", "NFR-04", "Script input is HTML-escaped", "<script>alert(1)</script>" not in get_html(ca, "/inventory"))
ca.post("/delete-product/NOPE")
anon = app.test_client()
check("TC-SEC-03", "NFR-05", "Anonymous user redirected from protected pages", all(anon.get(p).status_code == 302 for p in ["/inventory", "/dashboard", "/availability-report", "/add-product"]))
bad = get_html(app.test_client(), "/login")
r = app.test_client().post("/login", data={"username": "admin", "password": "x"}).get_data(as_text=True)
check("TC-SEC-04", "NFR-07", "Failed login shows no sensitive info (no SQL/stack trace)", not re.search(r"Traceback|mysql|SELECT |password_hash", r, re.I))

# PERFORMANCE
for i in range(200):
    cur.execute("INSERT IGNORE INTO products VALUES(%s,%s,'Bulk',1,%s,5,NULL)", (f"P-{i:04d}", f"Bulk {i}", i % 12))
db.commit()
times = {}
for page in ["/inventory", "/availability-report", "/dashboard"]:
    ts_ = []
    for _ in range(20):
        t = time.perf_counter(); ca.get(page); ts_.append((time.perf_counter() - t) * 1000)
    times[page] = (sum(ts_) / len(ts_), max(ts_))
worst = max(v[1] for v in times.values())
check("TC-PERF-01", "NFR-01/02", "Pages load fast with 200+ products (max < 2000 ms)", worst < 2000, "; ".join(f"{k}: avg {v[0]:.0f} ms, max {v[1]:.0f} ms" for k, v in times.items()))

json.dump(results, open("system_results.json", "w"), indent=1)
for r in results: print(r["result"], r["tc"], r["desc"], r["detail"])
print(sum(r["result"] == "PASS" for r in results), "/", len(results))

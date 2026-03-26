from flask import Flask, render_template, request, redirect, url_for, session, flash
import re

app = Flask(__name__)
app.secret_key = "shopeasy-secret-key-2024"

# ── PRODUCT CATALOGUE ──────────────────────────────────────────────────────────
PRODUCTS = [
    {"id": 1,  "name": "MacBook Pro",        "category": "Laptops",      "price": 1299.99, "emoji": "💻",
     "description": "Powerful laptop with M-series chip, perfect for developers and creatives."},
    {"id": 2,  "name": "iPhone 15",           "category": "Phones",       "price": 999.99,  "emoji": "📱",
     "description": "The latest iPhone with Dynamic Island and an advanced camera system."},
    {"id": 3,  "name": "Sony WH-1000XM5",    "category": "Headphones",   "price": 349.99,  "emoji": "🎧",
     "description": "Industry-leading noise cancelling headphones with 30-hour battery life."},
    {"id": 4,  "name": "Nike Air Max",        "category": "Shoes",        "price": 129.99,  "emoji": "👟",
     "description": "Classic Air Max cushioning with a modern twist. Available in multiple colours."},
    {"id": 5,  "name": "Samsung 4K TV",       "category": "TVs",          "price": 799.99,  "emoji": "📺",
     "description": "65-inch 4K QLED display with Dolby Vision and smart-home integration."},
    {"id": 6,  "name": "iPad Air",            "category": "Tablets",      "price": 599.99,  "emoji": "📟",
     "description": "Lightweight tablet with M1 chip and all-day battery life."},
    {"id": 7,  "name": "Canon EOS R50",       "category": "Cameras",      "price": 679.99,  "emoji": "📷",
     "description": "Compact mirrorless camera with 24MP sensor and 4K video recording."},
    {"id": 8,  "name": "Dyson V15 Detect",   "category": "Appliances",   "price": 649.99,  "emoji": "🌀",
     "description": "Cordless vacuum with laser dust detection and up to 60 min runtime."},
]

def get_product(product_id):
    return next((p for p in PRODUCTS if p["id"] == product_id), None)

def get_cart_items():
    cart = session.get("cart", {})
    items = []
    for pid, qty in cart.items():
        product = get_product(int(pid))
        if product:
            items.append({**product, "quantity": qty})
    return items

def cart_totals(items):
    subtotal = sum(i["price"] * i["quantity"] for i in items)
    shipping  = 0 if subtotal >= 50 else 5.99
    return round(subtotal, 2), round(subtotal + shipping, 2)

# ── HOME ───────────────────────────────────────────────────────────────────────
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", products=PRODUCTS)

# ── LOGIN ──────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Empty field validation
        if not username:
            return render_template("login.html", error="Email address is required.")
        if "@" not in username or "." not in username.split("@")[-1]:
            return render_template("login.html", error="Please enter a valid email address.")
        if not password:
            return render_template("login.html", error="Password is required.")

        # Credential check
        if username == "user@test.com" and password == "1234":
            session["user"] = username
            return "Login Success"   # plain-text response for Playwright assertion
        else:
            return render_template("login.html", error="Login Failed — invalid email or password.")

    return render_template("login.html")

# ── LOGOUT ─────────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

# ── SIGNUP ─────────────────────────────────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip()
        password         = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # Validation
        if not name:
            return render_template("signup.html", error="Full name is required.")
        if not email or "@" not in email:
            return render_template("signup.html", error="A valid email address is required.")
        if len(password) < 6:
            return render_template("signup.html", error="Password must be at least 6 characters.")
        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match.")

        session["user"] = email
        return render_template("signup.html", success=f"Account created for {email}! Welcome aboard.")

    return render_template("signup.html")

# ── SEARCH ─────────────────────────────────────────────────────────────────────
@app.route("/search")
def search():
    query = request.args.get("q", None)

    if query is None:
        return render_template("search.html", query=None, results=[])

    query_stripped = query.strip()

    if query_stripped == "":
        return render_template("search.html", query=query_stripped, results=[],
                               error_msg="Search query cannot be empty.")

    # Special-characters only guard
    if re.fullmatch(r"[^a-zA-Z0-9\s]+", query_stripped):
        return render_template("search.html", query=query_stripped, results=[],
                               error_msg="Please use regular characters in your search.")

    results = [p for p in PRODUCTS
               if query_stripped.lower() in p["name"].lower()
               or query_stripped.lower() in p["category"].lower()]

    return render_template("search.html", query=query_stripped, results=results)

# ── PRODUCT DETAIL ─────────────────────────────────────────────────────────────
@app.route("/product/<int:product_id>")
def product(product_id):
    p = get_product(product_id)
    if not p:
        return render_template("home.html", products=PRODUCTS), 404
    return render_template("product.html", product=p)

# ── CART — ADD ─────────────────────────────────────────────────────────────────
@app.route("/cart/add", methods=["POST"])
def cart_add():
    product_id = request.form.get("product_id", type=int)
    quantity   = request.form.get("quantity", 1, type=int)

    if not product_id or not get_product(product_id):
        flash("Product not found.", "error")
        return redirect(url_for("home"))

    cart = session.get("cart", {})
    key  = str(product_id)
    cart[key] = cart.get(key, 0) + quantity
    session["cart"] = cart

    p = get_product(product_id)
    flash(f"{p['name']} added to cart!", "success")
    return redirect(url_for("cart"))

# ── CART — REMOVE ──────────────────────────────────────────────────────────────
@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    product_id = request.form.get("product_id", type=int)
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("cart"))

# ── CART — VIEW ────────────────────────────────────────────────────────────────
@app.route("/cart")
def cart():
    items = get_cart_items()
    subtotal, total = cart_totals(items)
    return render_template("cart.html", cart_items=items, subtotal=subtotal, total=total)

# ── CHECKOUT ───────────────────────────────────────────────────────────────────
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items = get_cart_items()
    subtotal, total = cart_totals(items)

    if request.method == "POST":
        full_name      = request.form.get("full_name", "").strip()
        address        = request.form.get("address", "").strip()
        phone          = request.form.get("phone", "").strip()
        email          = request.form.get("email", "").strip()
        payment_method = request.form.get("payment_method", "").strip()

        # Validations
        if not full_name:
            return render_template("checkout.html", error="Full name is required.",
                                   cart_items=items, subtotal=subtotal, total=total)
        if not address:
            return render_template("checkout.html", error="Delivery address is required.",
                                   cart_items=items, subtotal=subtotal, total=total)
        if not phone or not re.fullmatch(r"[\d\s\+\-\(\)]{7,15}", phone):
            return render_template("checkout.html", error="A valid phone number is required.",
                                   cart_items=items, subtotal=subtotal, total=total)
        if not email or "@" not in email:
            return render_template("checkout.html", error="A valid email address is required.",
                                   cart_items=items, subtotal=subtotal, total=total)
        if not payment_method:
            return render_template("checkout.html", error="Please select a payment method.",
                                   cart_items=items, subtotal=subtotal, total=total)
        if not items:
            return render_template("checkout.html", error="Your cart is empty.",
                                   cart_items=items, subtotal=subtotal, total=total)

        # Clear cart and confirm
        session.pop("cart", None)
        return render_template("order_success.html", name=full_name, email=email)

    return render_template("checkout.html", cart_items=items, subtotal=subtotal, total=total)

# ── CONTACT ────────────────────────────────────────────────────────────────────
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name:
            return render_template("contact.html", error="Your name is required.")
        if not email or "@" not in email:
            return render_template("contact.html", error="A valid email address is required.")
        if not message:
            return render_template("contact.html", error="Message cannot be empty.")
        if len(message) > 2000:
            return render_template("contact.html", error="Message is too long (max 2000 characters).")

        return render_template("contact.html",
                               success="Message sent! We'll get back to you within 24 hours.")

    return render_template("contact.html")

# ── RUN ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
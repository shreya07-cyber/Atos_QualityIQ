# ShopEasy — Demo E-Commerce Website
### Person 1 deliverable for the AI Testing Platform project

---

## 🚀 Quick Start

```bash
cd demo_ecommerce
pip install flask
python app.py
```

Open → http://localhost:5000

---

## 📁 Folder Structure

```
demo_ecommerce/
├── app.py                  ← Flask application (all routes + logic)
├── requirements.txt
├── static/
│   └── style.css           ← Shared stylesheet
└── templates/
    ├── base.html           ← Navigation + flash messages
    ├── home.html           ← Home page + product grid
    ├── login.html          ← Login form
    ├── signup.html         ← Registration form
    ├── search.html         ← Product search
    ├── product.html        ← Product detail + Add to Cart
    ├── cart.html           ← Cart view
    ├── checkout.html       ← Checkout form
    ├── contact.html        ← Contact form
    └── order_success.html  ← Order confirmation
```

---

## 🔗 All Routes

| Route            | Method     | Purpose              |
|------------------|------------|----------------------|
| `/`              | GET        | Home page            |
| `/login`         | GET, POST  | User login           |
| `/logout`        | GET        | Logout               |
| `/signup`        | GET, POST  | User registration    |
| `/search?q=...`  | GET        | Product search       |
| `/product/<id>`  | GET        | Product detail page  |
| `/cart`          | GET        | View cart            |
| `/cart/add`      | POST       | Add item to cart     |
| `/cart/remove`   | POST       | Remove item          |
| `/checkout`      | GET, POST  | Checkout form        |
| `/contact`       | GET, POST  | Contact form         |

---

## 🧪 Test Credentials

```
Email:    user@test.com
Password: 1234
```

---

## 🤖 Automation-Ready Element IDs

All interactive elements have explicit IDs for Playwright automation:

### Login Page (`/login`)
| Element            | ID            |
|--------------------|---------------|
| Email input        | `#username`   |
| Password input     | `#password`   |
| Submit button      | `#login-btn`  |

### Signup Page (`/signup`)
| Element            | ID                  |
|--------------------|---------------------|
| Name input         | `#name`             |
| Email input        | `#email`            |
| Password input     | `#password`         |
| Confirm password   | `#confirm-password` |
| Submit button      | `#signup-btn`       |

### Search Page (`/search`)
| Element            | ID             |
|--------------------|----------------|
| Search input       | `#search-box`  |
| Search button      | `#search-btn`  |
| Results container  | `#search-results` |
| No-results div     | `#no-results`  |

### Product Page (`/product/<id>`)
| Element            | ID              |
|--------------------|-----------------|
| Product name       | `#product-name` |
| Product price      | `#product-price`|
| Qty minus          | `#qty-minus`    |
| Qty plus           | `#qty-plus`     |
| Add to cart button | `#add-cart-btn` |

### Cart Page (`/cart`)
| Element            | ID                         |
|--------------------|----------------------------|
| Cart items wrapper | `#cart-items`              |
| Per-item div       | `#cart-item-<id>`          |
| Remove button      | `#remove-btn-<id>`         |
| Subtotal           | `#cart-subtotal`           |
| Total              | `#cart-total`              |
| Checkout button    | `#checkout-btn`            |
| Empty cart div     | `#empty-cart`              |

### Checkout Page (`/checkout`)
| Element            | ID                  |
|--------------------|---------------------|
| Full name          | `#full-name`        |
| Address            | `#address`          |
| Phone              | `#phone`            |
| Email              | `#email`            |
| Card radio         | `#payment-card`     |
| PayPal radio       | `#payment-paypal`   |
| COD radio          | `#payment-cod`      |
| Place order button | `#checkout-btn`     |

### Contact Page (`/contact`)
| Element            | ID                      |
|--------------------|-------------------------|
| Name input         | `#contact-name`         |
| Email input        | `#contact-email`        |
| Subject input      | `#contact-subject`      |
| Message textarea   | `#contact-message`      |
| Submit button      | `#contact-submit-btn`   |

---

## ✅ Backend Validation Rules

| Feature  | Rule                                                        |
|----------|-------------------------------------------------------------|
| Login    | username == "user@test.com" AND password == "1234"          |
| Signup   | email contains "@", password ≥ 6 chars, passwords match    |
| Search   | empty → error, special chars only → error                  |
| Checkout | all fields required, phone regex validated                  |
| Contact  | name, valid email, non-empty message, message ≤ 2000 chars |

---

## 🔁 Playwright Assertion Strings

| Scenario              | Expected text in page     |
|-----------------------|---------------------------|
| Valid login           | `"Login Success"`         |
| Invalid login         | `"Login Failed"`          |
| Signup success        | `"Account created for"`   |
| Empty search          | `"cannot be empty"`       |
| Order placed          | `"Order Confirmed!"`      |
| Contact sent          | `"Message sent!"`         |

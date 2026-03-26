"""
automation_engine.py
--------------------
Playwright browser automation for all features.

WINDOWS FIX: On Windows, subprocess creation inside threads requires
ProactorEventLoop. We explicitly set it before launching Playwright.

EMAIL FIX: All inputs with type="email" are filled via page.evaluate()
instead of page.fill(). Browsers silently block form submission when a
type="email" field contains an invalid format (e.g. "notanemail"), so
Playwright never sees a page change -> assertion_engine returns ERROR.
Using evaluate() sets the value directly on the DOM element, bypassing
the browser's built-in HTML5 constraint validation entirely.
"""

import threading
import asyncio
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "http://localhost:5000"
TIMEOUT  = 8000  # ms


def _run_in_thread(fn, *args):
    result = [None]
    error  = [None]

    def target():
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = fn(*args)
        except Exception as e:
            error[0] = e
        finally:
            try:
                loop.close()
            except Exception:
                pass

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=60)

    if error[0]:
        raise error[0]
    if result[0] is None:
        return "<timeout/>"
    return result[0]


def _set_input(page, selector, value):
    """
    Sets an input value via JS to bypass HTML5 type='email' / type='tel'
    browser validation which silently blocks form submission.
    """
    page.evaluate(
        "([sel, val]) => { document.querySelector(sel).value = val; }",
        [selector, value]
    )


# ── LOGIN ──────────────────────────────────────────────────────────────────────
def _login_impl(username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/login", timeout=TIMEOUT)
            _set_input(page, "#username", username)
            _set_input(page, "#password", password)
            page.click("#login-btn")
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            return page.content()
        except PlaywrightTimeout:
            return "<timeout/>"
        finally:
            browser.close()

def run_login_test(username: str, password: str) -> str:
    return _run_in_thread(_login_impl, username, password)


# ── SIGNUP ─────────────────────────────────────────────────────────────────────
def _signup_impl(name, email, password, confirm_password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/signup", timeout=TIMEOUT)
            page.fill("#name", name)
            _set_input(page, "#email", email)          # type="email" — bypass
            page.fill("#password",         password)
            page.fill("#confirm-password", confirm_password)
            page.click("#signup-btn")
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            return page.content()
        except PlaywrightTimeout:
            return "<timeout/>"
        finally:
            browser.close()

def run_signup_test(name: str, email: str, password: str, confirm_password: str) -> str:
    return _run_in_thread(_signup_impl, name, email, password, confirm_password)


# ── SEARCH ─────────────────────────────────────────────────────────────────────
def _search_impl(query):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/search", timeout=TIMEOUT)
            page.fill("#search-box", query)
            page.click("#search-btn")
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            return page.content()
        except PlaywrightTimeout:
            return "<timeout/>"
        finally:
            browser.close()

def run_search_test(query: str) -> str:
    return _run_in_thread(_search_impl, query)


# ── CART ───────────────────────────────────────────────────────────────────────
def _cart_impl(product_id, quantity=1, action="add"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        try:
            if action == "remove":
                page.goto(f"{BASE_URL}/product/{product_id}", timeout=TIMEOUT)
                page.click("#add-cart-btn")
                page.wait_for_load_state("networkidle", timeout=TIMEOUT)
                page.click(f"#remove-btn-{product_id}")
                page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            else:
                page.goto(f"{BASE_URL}/product/{product_id}", timeout=TIMEOUT)
                for _ in range(quantity - 1):
                    page.click("#qty-plus")
                page.click("#add-cart-btn")
                page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            return page.content()
        except PlaywrightTimeout:
            return "<timeout/>"
        finally:
            browser.close()

def run_cart_test(product_id: int, quantity: int = 1, action: str = "add") -> str:
    return _run_in_thread(_cart_impl, product_id, quantity, action)


def _empty_cart_impl():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/cart", timeout=TIMEOUT)
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            return page.content()
        except PlaywrightTimeout:
            return "<timeout/>"
        finally:
            browser.close()

def run_empty_cart_test() -> str:
    return _run_in_thread(_empty_cart_impl)


# ── CHECKOUT ───────────────────────────────────────────────────────────────────
def _checkout_impl(full_name, address, phone, email, payment_method):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/product/1", timeout=TIMEOUT)
            page.click("#add-cart-btn")
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            page.goto(f"{BASE_URL}/checkout", timeout=TIMEOUT)
            page.fill("#full-name", full_name)
            page.fill("#address",   address)
            _set_input(page, "#phone", phone)          # type="tel" — bypass
            _set_input(page, "#email", email)          # type="email" — bypass
            radio_id = {
                "card":   "#payment-card",
                "paypal": "#payment-paypal",
                "cod":    "#payment-cod",
            }.get(payment_method, "#payment-card")
            page.click(radio_id)
            page.click("#checkout-btn")
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            return page.content()
        except PlaywrightTimeout:
            return "<timeout/>"
        finally:
            browser.close()

def run_checkout_test(full_name: str, address: str, phone: str,
                      email: str, payment_method: str) -> str:
    return _run_in_thread(_checkout_impl, full_name, address, phone, email, payment_method)


# ── CONTACT ────────────────────────────────────────────────────────────────────
def _contact_impl(name, email, subject, message):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        try:
            page.goto(f"{BASE_URL}/contact", timeout=TIMEOUT)
            page.fill("#contact-name",    name)
            _set_input(page, "#contact-email", email)  # type="email" — bypass
            page.fill("#contact-subject", subject)
            page.fill("#contact-message", message)
            page.click("#contact-submit-btn")
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            return page.content()
        except PlaywrightTimeout:
            return "<timeout/>"
        finally:
            browser.close()

def run_contact_test(name: str, email: str, subject: str, message: str) -> str:
    return _run_in_thread(_contact_impl, name, email, subject, message)


# ── ROUTER ─────────────────────────────────────────────────────────────────────
def run_test(feature: str, params: dict) -> str:
    feature = feature.lower()

    if feature == "login":
        return run_login_test(params["username"], params["password"])

    elif feature == "signup":
        return run_signup_test(
            params["name"], params["email"],
            params["password"], params["confirm_password"]
        )

    elif feature == "search":
        return run_search_test(params["query"])

    elif feature == "cart":
        if params.get("product_id") is None:
            return run_empty_cart_test()
        return run_cart_test(
            params["product_id"],
            params.get("quantity", 1),
            params.get("action", "add")
        )

    elif feature == "checkout":
        return run_checkout_test(
            params["full_name"], params["address"],
            params["phone"], params["email"],
            params["payment_method"]
        )

    elif feature == "contact":
        return run_contact_test(
            params["name"], params["email"],
            params.get("subject", ""), params["message"]
        )

    return "<unsupported_feature/>"
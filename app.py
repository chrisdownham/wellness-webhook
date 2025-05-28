import os
import time
import traceback
import requests
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

# Configuration
PAGE_URL    = "https://www.wellnessliving.com/rs/lead-add.html?k_business=314287&k_skin=202951"
CAPTCHA_KEY = os.environ.get("CAPTCHA_KEY")

app = Flask(__name__)

def solve_recaptcha(site_key: str, page_url: str) -> str:
    # 1) Submit the CAPTCHA challenge
    resp = requests.get("http://2captcha.com/in.php", params={
        "key": CAPTCHA_KEY,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
    })
    if resp.status_code != 200 or "OK|" not in resp.text:
        raise RuntimeError(f"2Captcha submit error: {resp.text}")
    captcha_id = resp.text.split("|")[1]

    # 2) Poll for solution
    for _ in range(20):
        time.sleep(5)
        result = requests.get("http://2captcha.com/res.php", params={
            "key": CAPTCHA_KEY,
            "action": "get",
            "id": captcha_id,
        }).text
        if result.startswith("OK|"):
            return result.split("|")[1]
        if result != "CAPCHA_NOT_READY":
            raise RuntimeError(f"2Captcha error: {result}")
    raise RuntimeError("CAPTCHA solving timed out")

@app.route("/new-lead", methods=["POST"])
def handle_new_lead():
    data = request.json or {}
    first_name = data.get("first_name")
    last_name  = data.get("last_name")
    email      = data.get("email")
    phone      = data.get("phone")

    # Validate inputs
    if not all([first_name, last_name, email, phone]):
        return jsonify({"status":"error","message":"Missing required fields"}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to public lead form
            page.goto(PAGE_URL, wait_until="networkidle")

            # Extract reCAPTCHA site-key
            site_key = page.locator(".g-recaptcha").get_attribute("data-sitekey")

            # Solve reCAPTCHA
            token = solve_recaptcha(site_key, PAGE_URL)

            # Inject the token
            page.evaluate(
                "(token) => document.querySelector('textarea[name=\"g-recaptcha-response\"]').value = token",
                token
            )

            # Fill out form fields
            page.fill('input[name="first_name"]', first_name)
            page.fill('input[name="last_name"]',  last_name)
            page.fill('input[name="email"]',      email)
            page.fill('input[name="phone"]',      phone)

            # Submit the form
            page.click('button[type="submit"]')
            browser.close()

        return jsonify({"status":"success","submitted":email}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status":"error","message":str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

@app.route("/new-lead", methods=["POST"])
def handle_new_lead():
    data = request.json
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    email = data.get("email", "")
    phone = data.get("phone", "")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.wellnessliving.com/rs/lead-add.html?k_business=314287&k_skin=202951")
        page.fill('input[name="first_name"]', first_name)
        page.fill('input[name="last_name"]', last_name)
        page.fill('input[name="email"]', email)
        page.fill('input[name="phone"]', phone)
        page.click('button[type="submit"]')
        browser.close()

    return jsonify({"status": "success", "submitted": email})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

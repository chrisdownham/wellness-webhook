import os
import traceback
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Credentials stored in Railway environment variables
WL_EMAIL = os.environ["WL_EMAIL"]
WL_PASSWORD = os.environ["WL_PASSWORD"]

app = Flask(__name__)

@app.route("/new-lead", methods=["POST"])
def handle_new_lead():
    data = request.json or {}
    first_name = data.get("first_name", "")
    last_name  = data.get("last_name", "")
    email      = data.get("email", "")
    phone      = data.get("phone", "")
    redemption = data.get("redemption_code", "")  # optional

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 1) Login to Staff portal
            page.goto(
                "https://www.wellnessliving.com/login",
                timeout=60000,
                wait_until="networkidle"
            )
            page.fill('input[name="username"]', WL_EMAIL)
            page.fill('input[name="password"]', WL_PASSWORD)
            page.click('button:has-text("Sign in")')
            page.wait_for_load_state("networkidle", timeout=60000)

            # 2) Navigate to Add New Client form
            page.goto(
                "https://www.wellnessliving.com/rs/lead-add.html?k_business=314287&k_skin=202951",
                timeout=60000,
                wait_until="networkidle"
            )
            page.wait_for_load_state("domcontentloaded", timeout=30000)

            # 3) Fill out the form by placeholder
            page.get_by_placeholder("First name").fill(first_name)
            page.get_by_placeholder("Last name").fill(last_name)
            page.get_by_placeholder("Email").fill(email)
            page.get_by_placeholder("Cell phone").fill(phone)

            # 4) Optional Redemption code
            if redemption:
                page.get_by_placeholder("Redemption code").fill(redemption)

            # 5) Select Home location
            page.get_by_role("combobox", name="Home location") \
                .select_option(label="R1SE @ Kelham")

            # 6) Submit
            page.get_by_role("button", name="Add").click()

            # Wait briefly to ensure submission
            page.wait_for_timeout(2000)

            browser.close()

        return jsonify({"status": "success", "submitted": email}), 200

    except PWTimeout as e:
        print("❌ Timeout during automation:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Timeout during navigation or fill"}), 504

    except Exception as e:
        print("❌ Unexpected error:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

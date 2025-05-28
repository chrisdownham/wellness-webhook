import os
import traceback
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ← Make sure these are set in Railway Variables
WL_EMAIL    = os.environ["WL_EMAIL"]
WL_PASSWORD = os.environ["WL_PASSWORD"]

app = Flask(__name__)

@app.route("/new-lead", methods=["POST"])
def handle_new_lead():
    data = request.json or {}
    first_name = data.get("first_name", "")
    last_name  = data.get("last_name", "")
    email      = data.get("email", "")
    phone      = data.get("phone", "")
    redemption = data.get("redemption_code", "")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 1) Login — redirect back to Staff dashboard
            page.goto(
                "https://www.wellnessliving.com/login?url_return=%2FWl%2FStaff%2FLocation.html",
                timeout=60000,
                wait_until="networkidle"
            )
            page.locator("#template-passport-login").fill(WL_EMAIL)
            page.locator("#template-passport-password").fill(WL_PASSWORD)
            page.locator("#passport_login_small span").click()
            page.wait_for_load_state("networkidle", timeout=60000)

            # 2) Click "Add Client"
            page.get_by_role("button", name="Add Client").wait_for(timeout=30000)
            page.get_by_role("button", name="Add Client").click()

            # 3) Wait for modal
            page.wait_for_selector("text=Add New Client", timeout=30000)

            # 4) Fill the form
            page.get_by_placeholder("First name").fill(first_name)
            page.get_by_placeholder("Last name").fill(last_name)
            page.get_by_placeholder("Email").fill(email)
            page.get_by_placeholder("Cell phone").fill(phone)
            if redemption:
                page.get_by_placeholder("Redemption code").fill(redemption)

            # 5) Select Home location
            page.get_by_role("combobox", name="Home location") \
                .select_option(label="R1SE @ Kelham")

            # 6) Submit
            page.get_by_role("button", name="Add").click()
            page.wait_for_timeout(2000)

            browser.close()

        return jsonify({"status": "success", "submitted": email}), 200

    except PWTimeout as e:
        print("❌ Timeout step:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Timeout during automation"}), 504

    except Exception as e:
        print("❌ Unexpected error:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

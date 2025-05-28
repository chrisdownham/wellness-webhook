import os
import traceback
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Credentials from Railway env vars
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

            # 1) Login via the known template IDs
            page.goto(
                "https://www.wellnessliving.com/login/r1se_yoga",
                timeout=60000,
                wait_until="networkidle"
            )
            page.locator("#template-passport-login").fill(WL_EMAIL)
            page.locator("#template-passport-login").press("Tab")
            page.locator("#template-passport-password").fill(WL_PASSWORD)
            page.locator("#passport_login_small span").click()
            page.wait_for_load_state("networkidle", timeout=60000)

            # 2) Go to Staff dashboard
            page.goto(
                "https://www.wellnessliving.com/Wl/Staff/Location.html",
                timeout=60000,
                wait_until="networkidle"
            )

            # 3) Open Add Client
            page.get_by_role("button", name="Add Client").wait_for(timeout=30000)
            page.get_by_role("button", name="Add Client").click()
            page.wait_for_selector("text=Add New Client", timeout=30000)

            # 4) Fill modal fields
            page.wait_for_selector('input[placeholder="First name"]', timeout=30000)
            page.fill('input[placeholder="First name"]', first_name)
            page.wait_for_selector('input[placeholder="Last name"]', timeout=30000)
            page.fill('input[placeholder="Last name"]', last_name)
            page.wait_for_selector('input[placeholder="Email"]', timeout=30000)
            page.fill('input[placeholder="Email"]', email)
            page.wait_for_selector('input[placeholder="Cell phone"]', timeout=30000)
            page.fill('input[placeholder="Cell phone"]', phone)
            if redemption:
                page.wait_for_selector('input[placeholder="Redemption code"]', timeout=30000)
                page.fill('input[placeholder="Redemption code"]', redemption)

            # 5) Select Home location
            combo = page.get_by_role("combobox", name="Home location")
            combo.wait_for(timeout=30000)
            combo.select_option(label="R1SE @ Kelham")

            # 6) Submit
            button = page.get_by_role("button", name="Add")
            button.wait_for(timeout=30000)
            button.click()

            page.wait_for_timeout(2000)
            browser.close()

        return jsonify({"status": "success", "submitted": email}), 200

    except PWTimeout as e:
        print("❌ Timeout during automation:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Timeout"}), 504

    except Exception as e:
        print("❌ Unexpected error:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

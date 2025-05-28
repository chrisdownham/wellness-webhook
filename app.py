import os
import traceback
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

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

            # Login
            print("🔑 Navigating to login")
            page.goto("https://www.wellnessliving.com/login/r1se_yoga",
                      timeout=60000, wait_until="networkidle")
            print("🔑 Filling email")
            page.get_by_label("Email").fill(WL_EMAIL)
            print("🔑 Filling password")
            page.get_by_label("Password").fill(WL_PASSWORD)
            print("🔑 Clicking Sign in")
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_load_state("networkidle", timeout=60000)

            # Go to Staff dashboard
            print("📋 Navigating to Staff dashboard")
            page.goto("https://www.wellnessliving.com/Wl/Staff/Location.html",
                      timeout=60000, wait_until="networkidle")

            # Click Add Client
            print("➕ Waiting for Add Client button")
            page.get_by_role("button", name="Add Client").wait_for(timeout=30000)
            print("➕ Clicking Add Client")
            page.get_by_role("button", name="Add Client").click()

            # Wait for modal
            print("📝 Waiting for Add New Client modal")
            page.wait_for_selector('text=Add New Client', timeout=30000)

            # Fill First name
            print("✍️ Waiting for First name input")
            page.wait_for_selector('input[placeholder="First name"]', timeout=30000)
            print("✍️ Filling First name")
            page.fill('input[placeholder="First name"]', first_name)

            # Fill Last name
            print("✍️ Waiting for Last name input")
            page.wait_for_selector('input[placeholder="Last name"]', timeout=30000)
            print("✍️ Filling Last name")
            page.fill('input[placeholder="Last name"]', last_name)

            # Fill Email
            print("✉️ Waiting for Email input")
            page.wait_for_selector('input[placeholder="Email"]', timeout=30000)
            print("✉️ Filling Email")
            page.fill('input[placeholder="Email"]', email)

            # Fill Cell phone
            print("📱 Waiting for Cell phone input")
            page.wait_for_selector('input[placeholder="Cell phone"]', timeout=30000)
            print("📱 Filling Cell phone")
            page.fill('input[placeholder="Cell phone"]', phone)

            # Optional Redemption code
            if redemption:
                print("🔖 Waiting for Redemption code input")
                page.wait_for_selector('input[placeholder="Redemption code"]', timeout=30000)
                print("🔖 Filling Redemption code")
                page.fill('input[placeholder="Redemption code"]', redemption)

            # Select Home location
            print("🏠 Waiting for Home location dropdown")
            combo = page.get_by_role("combobox", name="Home location")
            combo.wait_for(timeout=30000)
            print("🏠 Selecting R1SE @ Kelham")
            combo.select_option(label="R1SE @ Kelham")

            # Submit
            print("✅ Waiting for Add button")
            page.get_by_role("button", name="Add").wait_for(timeout=30000)
            print("✅ Clicking Add")
            page.get_by_role("button", name="Add").click()

            # Give it a moment
            page.wait_for_timeout(2000)
            browser.close()

        print("🎉 Success for", email)
        return jsonify({"status": "success", "submitted": email}), 200

    except PWTimeout as e:
        print("❌ Timeout during step:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Timeout during automation"}), 504

    except Exception as e:
        print("❌ Unexpected error:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

import os
import traceback
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ⚠️ Make sure to store these securely in Railway's Environment Variables:
WL_EMAIL = os.environ.get("WL_EMAIL", "ctdownham@googlemail.com")
WL_PASSWORD = os.environ.get("WL_PASSWORD", "168421ctd")

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
            page.goto("https://www.wellnessliving.com/login", timeout=60000, wait_until="networkidle")
            page.fill('input[name="username"]', WL_EMAIL)
            page.fill('input[name="password"]', WL_PASSWORD)
            page.click('button:has-text("Sign in")')
            page.wait_for_load_state("networkidle", timeout=60000)

            # 2) Go to Add Client form
            page.goto("https://www.wellnessliving.com/rs/lead-add.html?k_business=314287&k_skin=202951",
                      wait_until="networkidle", timeout=60000)

            # 3) Wait for form to be visible
            page.wait_for_selector('text=First name', timeout=30000)

            # 4) Fill fields:
            page.get_by_placeholder("First name").fill(first_name)
            page.get_by_placeholder("Last name").fill(last_name)
            page.get_by_placeholder("Email").fill(email)
            page.get_by_placeholder("Cell phone").fill(phone)

            # 5) (Optional) Redemption code
            if redemption:
                page.get_by_placeholder("Redemption code").fill(redemption)

            # 6) Home location dropdown
            # Use the accessible label "Home location" / combobox role
            page.get_by_role("combobox", name="Home location").select_option(label="R1SE @ Kelham")

            # 7) Submit the form by clicking the Add button
            page.get_by_role("button", name="Add").click()

            # Wait a moment for the modal to close / submission to complete
            page.wait_for_timeout(2000)
            browser.close()

        return jsonify({"status": "success", "submitted": email}), 200

    except PWTimeout as e:
        print("❌ Timeout when automating lead creation:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Timeout"}), 504

    except Exception as e:
        print("❌ Error handling new lead:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

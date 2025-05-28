import os
import traceback
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Pull these in from Railway’s Environment Variables
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
    redemption = data.get("redemption_code", "")  # optional

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 1) Login to your studio's custom path (no hard-coded semicolon!)
            page.goto(
                "https://www.wellnessliving.com/login/r1se_yoga",
                timeout=60000,
                wait_until="networkidle"
            )

            # Fill by visible labels
            page.get_by_label("Email").fill(WL_EMAIL)
            page.get_by_label("Password").fill(WL_PASSWORD)
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_load_state("networkidle", timeout=60000)

            # 2) Navigate to the staff Add Client form
            page.goto(
                "https://www.wellnessliving.com/rs/lead-add.html?k_business=314287&k_skin=202951",
                timeout=60000,
                wait_until="networkidle"
            )
            page.wait_for_load_state("domcontentloaded", timeout=30000)

            # 3) Fill out the “Add Client” modal
            page.get_by_placeholder("First name").fill(first_name)
            page.get_by_placeholder("Last name").fill(last_name)
            page.get_by_placeholder("Email").fill(email)
            page.get_by_placeholder("Cell phone").fill(phone)
            if redemption:
                page.get_by_placeholder("Redemption code").fill(redemption)

            # 4) Select “R1SE @ Kelham” for Home location
            page.get_by_role("combobox", name="Home location") \
                .select_option(label="R1SE @ Kelham")

            # 5) Submit by clicking “Add”
            page.get_by_role("button", name="Add").click()
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

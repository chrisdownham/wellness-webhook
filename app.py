import traceback
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import os

app = Flask(__name__)

@app.route("/new-lead", methods=["POST"])
def handle_new_lead():
    data = request.json or {}
    first_name = data.get("first_name", "")
    last_name  = data.get("last_name", "")
    email      = data.get("email", "")
    phone      = data.get("phone", "")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to the WellnessLiving lead form
            page.goto(
                "https://www.wellnessliving.com/rs/lead-add.html?k_business=314287&k_skin=202951",
                wait_until="networkidle",
                timeout=60000
            )

            # Fill out the form using placeholder selectors
            page.wait_for_selector('input[placeholder="First Name"]', timeout=60000)
            page.fill('input[placeholder="First Name"]', first_name)

            page.wait_for_selector('input[placeholder="Last Name"]', timeout=60000)
            page.fill('input[placeholder="Last Name"]', last_name)

            page.wait_for_selector('input[placeholder="Email"]', timeout=60000)
            page.fill('input[placeholder="Email"]', email)

            page.wait_for_selector('input[placeholder="Phone"]', timeout=60000)
            page.fill('input[placeholder="Phone"]', phone)

            # Submit the form
            page.click('button[type="submit"]')

            browser.close()

        return jsonify({"status": "success", "submitted": email}), 200

    except PWTimeout as e:
        print("❌ Timeout navigating or filling the form:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Navigation or fill timeout"}), 504

    except Exception as e:
        print("❌ Error handling new lead:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

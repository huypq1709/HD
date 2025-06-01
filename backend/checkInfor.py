from flask import jsonify
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import Flask-CORS
from selenium.webdriver.common.bidi import console

app = Flask(__name__)
CORS(app)  # Áp dụng CORS cho tất cả các route


@app.route("/check-phone", methods=["POST"])
def check_phone():
    data = request.get_json()
    phone = data.get("phone", "")
    if not phone or len(phone) != 10 or not phone.isdigit():
        return jsonify({"error": "Invalid phone number"}), 400

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from bs4 import BeautifulSoup
    import time

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://hdfitnessyoga.timesoft.vn/")

        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("Vuongvv")
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "Password"))).send_keys("291199")
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()

        time.sleep(5)

        radio_all = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "radio_0"))
        )
        radio_all.click()
        time.sleep(0.5)

        search_input = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
        )
        search_input.clear()
        search_input.send_keys(phone)
        search_input.send_keys(Keys.ENTER)

        time.sleep(0.5)

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")

        table_body = soup.find("tbody", class_="show-table-ready")
        rows = table_body.find_all("tr") if table_body else []

        data_list = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            # 0: Tên khách hàng
            name_elem = cols[0].find("span", class_="ng-binding")
            name = name_elem.text.strip() if name_elem else ""

            # 2: Số điện thoại
            phone_text = cols[2].text.strip()

            # 3: Dịch vụ
            service_text = cols[3].text.strip()

            # 4: Còn lại (span đầu tiên)
            remaining = ""
            span_list = cols[5].find_all("span")
            if span_list:
                remaining = span_list[0].text.strip()

            # 5: Ngày bắt đầu
            start_date = cols[6].text.strip()

            # 6: Ngày hết hạn
            end_date = cols[7].text.strip()

            # Trạng thái
            status_span = row.find("span", class_=lambda value: value and "status-" in value)
            status = status_span.text.strip() if status_span else ""

            data_list.append({
                "name": name,
                "phone": phone_text,
                "service": service_text,
                "remaining": remaining,
                "start_date": start_date,
                "end_date": end_date,
                "status": status
            })

        return jsonify({"results": data_list})

    except Exception as e:
        return jsonify({"error": f"Error during automation: {str(e)}"}), 500
    finally:
        driver.quit()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
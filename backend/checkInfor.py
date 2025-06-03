

from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService  # Nên dùng
from bs4 import BeautifulSoup
import time
import tempfile  # Thêm import này cho giải pháp thư mục tạm
import shutil  # Thêm import này để xóa thư mục tạm




app = Flask(__name__)
CORS(app)



@app.route("/check-phone", methods=["POST"])
def check_phone():
    data = request.get_json()
    phone_number = data.get("phone", "")
    if not phone_number or len(phone_number) != 10 or not phone_number.isdigit():
        return jsonify({"error": "Invalid phone number"}), 400

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = ChromeService(executable_path='/usr/local/bin/chromedriver')
    print("DEBUG: checkInfor.py - Đã cấu hình ChromeService") # PRINT D

    driver = None
    try:
        print("DEBUG: checkInfor.py - Chuẩn bị khởi tạo WebDriver") # PRINT E
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://hdfitnessyoga.timesoft.vn/")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys(
            "Vuongvv")
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
        search_input.send_keys(phone_number)
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
        error_message = f"Error in check_phone: {type(e).__name__} - {str(e)}"
        print(f"DEBUG: checkInfor.py - GẶP LỖI: {error_message}") # PRINT ERROR
        return jsonify({"error": error_message}), 500
    finally:
        print("DEBUG: checkInfor.py - Vào khối finally") # PRINT FINALLY
        if driver:
            driver.quit()
            print("DEBUG: checkInfor.py - Đã gọi driver.quit()") # PRINT QUIT
        # ... (phần xử lý temp_user_data_dir nếu có) ...


# Dòng này chỉ để chạy test trực tiếp file Python, không ảnh hưởng khi chạy với Gunicorn
if __name__ == "__main__":
    print("DEBUG: checkInfor.py - Chạy ở chế độ __main__ (test cục bộ)") # PRINT MAIN
    app.run(host="0.0.0.0", port=5000, debug=True) # Đã sửa lại cổng cho khớp


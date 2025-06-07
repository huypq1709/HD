from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import traceback
from selenium.webdriver.chrome.service import Service as ChromeService
import time

app = Flask(__name__)
CORS(app)

automation_results = {}

def run_automation(phone, customer_type):
    """Hàm thực hiện các bước tự động hóa Selenium và lưu kết quả."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # Tối ưu: tắt tải ảnh, font, stylesheet
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.fonts": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    result = None

    try:
        driver.get("https://hdfitnessyoga.timesoft.vn/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("Vuongvv")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Password"))).send_keys("291199")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()

        # Đợi trang load sau khi đăng nhập
        time.sleep(5)

        # Đợi radio_all xuất hiện và click
        radio_all = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "radio_0"))
        )
        radio_all.click()
        time.sleep(1)  # Đợi radio được chọn

        # Đợi input search xuất hiện
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
        )
        search_input.clear()
        search_input.send_keys(phone)
        search_input.send_keys(Keys.ENTER)

        # Đợi kết quả tìm kiếm load
        time.sleep(2)

        # Kiểm tra kết quả tìm kiếm
        try:
            # Đợi tối đa 15 giây cho kết quả tìm kiếm
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//td[@class='z-index-2 sticky-column-left zindex1000']/div[@class='d-flex align-items-center']"))
            )
            result = "found"
        except:
            try:
                # Đợi tối đa 15 giây cho thông báo không tìm thấy
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located(
                    (By.XPATH, "//td[@colspan='12' and contains(text(), 'Không tìm thấy bản ghi nào')]")))
                # Đợi thêm 1 giây để đảm bảo thông báo đã hiển thị đầy đủ
                time.sleep(1)
                result = "not_found"
            except:
                result = "error_checking"

        print(f"Kết quả tự động hóa cho số điện thoại {phone}: {result}, Loại khách hàng: {customer_type}")

    except Exception as e:
        error_message = f"Lỗi tự động hóa (ĐT: {phone}, Loại: {customer_type}): {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        result = "automation_error"
    finally:
        if 'driver' in locals():
            driver.quit()
        automation_results[phone] = result

@app.route("/process-phone-from-screen", methods=["POST"])
def process_phone_from_screen():
    data = request.get_json()
    phone = data.get("phoneNumber")
    customer_type = data.get("customerType")
    if phone and customer_type:
        thread = Thread(target=run_automation, args=(phone, customer_type))
        thread.start()
        return jsonify({"message": "Đang xử lý yêu cầu..."}), 202
    else:
        return jsonify({"error": "Không tìm thấy 'phoneNumber' hoặc 'customerType' trong yêu cầu"}), 400

@app.route("/check-automation-result/<phone>", methods=["GET"])
def check_automation_result(phone):
    if phone in automation_results:
        result = automation_results.pop(phone)  # Lấy và xóa kết quả sau khi trả về
        return jsonify({"automation_result": result}), 200
    else:
        return jsonify({"message": "Đang xử lý hoặc không tìm thấy kết quả."}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
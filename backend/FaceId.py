from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
import time
import traceback

app = Flask(__name__)
CORS(app)

@app.route("/initiate-faceid", methods=["POST"])
def initiate_faceid():
    data = request.get_json()
    phone = data.get("phone", "")
    print(f"Flask received phone number: {phone}")

    if not phone or len(phone) != 10 or not phone.isdigit():
        return jsonify({"error": "Invalid phone number"}), 400

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
    service = ChromeService(executable_path='/usr/local/bin/chromedriver')
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://hdfitnessyoga.timesoft.vn/")
        print("Flask: Opened the website")

        # Đăng nhập
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("Vuongvv")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Password"))).send_keys("291199")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        print("Flask: Logged in")

        # Đợi trang load sau khi đăng nhập
        time.sleep(3)

        # Đợi radio_all xuất hiện và click
        radio_all = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "radio_0"))
        )
        radio_all.click()
        time.sleep(1)  # Đợi radio được chọn
        print("Flask: Clicked 'Tất cả'")

        # Đợi input search xuất hiện
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
        )
        search_input.clear()
        search_input.send_keys(phone)
        search_input.send_keys(Keys.ENTER)
        print(f"Flask: Searched for phone number: {phone}")

        # Đợi kết quả tìm kiếm load
        time.sleep(1)

        # Kiểm tra kết quả tìm kiếm
        try:
            # Đợi bảng kết quả xuất hiện
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.show-table-ready"))
            )
            # Đợi thêm 1 giây để đảm bảo dữ liệu load đầy đủ
            time.sleep(1)

            html_content = driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")
            no_records_element = soup.find("td", colspan="12", string="Không tìm thấy bản ghi nào")
            if no_records_element:
                print("Flask: No records found")
                return jsonify({"status": "not_found", "message": "No customer information found"}), 200
            else:
                print("Flask: Records found, proceeding to click customer name")
                try:
                    table_body = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//tbody[@class='show-table-ready']"))
                    )
                    first_row = table_body.find_element(By.XPATH, "./tr[1]")
                    name_element = WebDriverWait(first_row, 5).until(
                        EC.presence_of_element_located((By.XPATH, ".//td[1]//span[@class='ng-binding']"))
                    )
                    customer_name = name_element.text.strip()
                    print(f"Flask: Customer name found: {customer_name}")
                    customer_phone = phone
                except Exception as e:
                    print(f"Flask: Could not find customer name from table: {e}")
                    customer_name = "N/A"
                    customer_phone = phone

                # Click vào tên khách hàng
                customer_name_span = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//tbody[@class='show-table-ready']/tr[1]//span[@role='button' and contains(@ng-click, 'showEditModal')]"))
                )
                customer_name_span.click()
                print("Flask: Clicked on customer name")
                time.sleep(1)  # Đợi modal hiển thị

                # Click nút đăng ký khuôn mặt
                register_face_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='button' and @class='btn btn-success' and contains(@ng-click, 'registerFace')]"))
                )
                register_face_button.click()
                print("Flask: Clicked on 'ĐK khuôn mặt(F6)'")
                time.sleep(1)  # Đợi modal đăng ký khuôn mặt hiển thị

                # Chọn radio "Từ ảnh chụp trên FaceId"
                faceid_radio_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//md-radio-button[@aria-label='Ảnh chụp Snap trên FaceId']"))
                )
                faceid_radio_button.click()
                print("Flask: Selected 'Từ ảnh chụp trên FaceId'")
                time.sleep(1)  # Đợi radio được chọn

                # Click checkbox "Thiết lập làm ảnh đại diện"
                set_as_avatar_checkbox = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//md-checkbox[@aria-label='Thiết lập làm ảnh đại diện']"))
                )
                set_as_avatar_checkbox.click()
                print("Flask: Clicked on 'Thiết lập làm ảnh đại diện'")
                time.sleep(1)  # Đợi checkbox được chọn

                # Click vào ảnh đầu tiên
                first_snap_image = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'col-sm-4') and contains(@class, 'ng-scope')][1]//img"))
                )
                first_snap_image.click()
                print("Flask: Selected the first snap image in the row")
                time.sleep(1)  # Đợi ảnh được chọn

                # Click nút "Đăng ký khuôn mặt (F6)"
                register_new_face_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//button[@type='button' and @class='btn btn-success' and contains(@ng-click, 'regNewFaceId') and @ng-show='selectedIndex==0']"))
                )
                register_new_face_button.click()
                print("Flask: Clicked on 'Đăng ký khuôn mặt (F6)'")
                time.sleep(1)  # Đợi quá trình đăng ký hoàn tất

                return jsonify({
                    "status": "face_registration_completed",
                    "message": "Face registration steps completed",
                    "name": customer_name,
                    "phone": customer_phone
                }), 200

        except Exception as e:
            print(f"Flask: Error during face registration steps: {str(e)}")
            return jsonify({"status": "error", "message": f"Error during face registration steps: {str(e)}"}), 500

    except Exception as e:
        print(f"Flask: Error during automation: {str(e)}")
        return jsonify({"status": "error", "message": f"Error during automation: {str(e)}"}), 500
    finally:
        print("Flask: Closing the browser")
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("Flask app started on port 5005")
    app.run(host="0.0.0.0", port=5005, debug=True)
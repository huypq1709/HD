from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time

app = Flask(__name__)
CORS(app)

@app.route("/initiate-faceid", methods=["POST"])
def initiate_faceid():
    data = request.get_json()
    phone = data.get("phone", "")
    print(f"Flask received phone number: {phone}")

    if not phone or len(phone) != 10 or not phone.isdigit():
        print("Flask: Invalid phone number format")
        return jsonify({"error": "Invalid phone number"}), 400

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://hdfitnessyoga.timesoft.vn/")
        print("Flask: Opened the website")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("Vuongvv")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Password"))).send_keys("291199")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        print("Flask: Logged in")

        time.sleep(5)

        radio_all = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "radio_0"))
        )
        radio_all.click()
        print("Flask: Clicked 'Tất cả'")
        time.sleep(1)

        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
        )
        search_input.clear()
        search_input.send_keys(phone)
        search_input.send_keys(Keys.ENTER)
        print(f"Flask: Searched for phone number: {phone}")
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
                # **Lấy tên khách hàng từ bảng**
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
                    customer_phone = phone  # Số điện thoại đã có từ trước

                except Exception as e:
                    print(f"Flask: Could not find customer name from table: {e}")
                    customer_name = "N/A"
                    customer_phone = phone

                customer_name_span = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//tbody[@class='show-table-ready']/tr[1]//span[@role='button' and contains(@ng-click, 'showEditModal')]"))
                )
                customer_name_span.click()
                print("Flask: Clicked on customer name")
                time.sleep(1)

                # **Bước 1: Nhấp vào nút "ĐK khuôn mặt(F6)"**
                register_face_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@type='button' and @class='btn btn-success' and contains(@ng-click, 'registerFace')]"))
                )
                register_face_button.click()
                print("Flask: Clicked on 'ĐK khuôn mặt(F6)'")
                time.sleep(1)

                # **Bước 2: Chọn radio button "Từ ảnh chụp trên FaceId"**
                faceid_radio_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//md-radio-button[@aria-label='Ảnh chụp Snap trên FaceId']"))
                )
                faceid_radio_button.click()
                print("Flask: Selected 'Từ ảnh chụp trên FaceId'")
                time.sleep(1)

                # **Bước 4: Tích vào ô "Thiết lập làm ảnh đại diện"**
                set_as_avatar_checkbox = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//md-checkbox[@aria-label='Thiết lập làm ảnh đại diện']"))
                )
                set_as_avatar_checkbox.click()
                print("Flask: Clicked on 'Thiết lập làm ảnh đại diện'")
                time.sleep(1)

                # **Bước 5: Chọn hình ảnh đầu tiên trong hàng**
                first_snap_image = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'col-sm-4') and contains(@class, 'ng-scope')][1]//img"))
                )
                first_snap_image.click()
                print("Flask: Selected the first snap image in the row")
                time.sleep(1)

                # **Bước 7: Bấm vào nút "Đăng ký khuôn mặt (F6)" thứ hai**
                register_new_face_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//button[@type='button' and @class='btn btn-success' and contains(@ng-click, 'regNewFaceId') and @ng-show='selectedIndex==0']"))
                )
                register_new_face_button.click()
                print("Flask: Clicked on 'Đăng ký khuôn mặt (F6)'")

                time.sleep(1)

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
        driver.quit()

if __name__ == "__main__":
    print("Flask app started on port 5005")
    app.run(host="0.0.0.0", port=5005, debug=True)
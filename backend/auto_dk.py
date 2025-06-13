# automation_app.py
import os
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, \
    ElementClickInterceptedException

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://13.229.230.76/", "http://localhost:5173"]}})


# --- CẤU HÌNH SELENIUM ---
def _initialize_driver():
    """Khởi tạo và trả về một instance WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Tối ưu: tắt tải ảnh, font, stylesheet (và JS nếu không cần)
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.fonts": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        # "profile.managed_default_content_settings.javascript": 2,  # Bật nếu KHÔNG cần JS
    }
    chrome_options.add_experimental_option("prefs", prefs)
    try:
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except WebDriverException as e:
        print(f"Lỗi khởi tạo Chrome driver: {e}")
        return None

def _login_to_timesoft(driver: webdriver.Chrome):
    """Thực hiện các bước đăng nhập vào Timesoft."""
    try:
        driver.get("https://hdfitnessyoga.timesoft.vn/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("Vuongvv")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "Password"))).send_keys("291199")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
        # Đợi trang chính xuất hiện (ví dụ: kiểm tra một phần tử đặc trưng sau đăng nhập)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "radio_0")))
        return True
    except TimeoutException:
        return False
    except Exception as e:
        return False


# automation_app.py

# ... (các imports khác)

# Cập nhật ánh xạ gói tập sang index cho GYM
MEMBERSHIP_INDEX_MAP_GYM = {
    "1 year": 2,  # GYM 12 THÁNG
    "1 month": 3,  # GYM 1 THÁNG
    "1 day": 4,  # GYM 1 NGÀY
    "3 months": 5,  # GYM 3 THÁNG
    "6 months": 6,  # GYM 6 THÁNG
}

# Ánh xạ gói tập sang index cho YOGA
MEMBERSHIP_INDEX_MAP_YOGA = {
    "1 month": 1,  # Yoga 1T 12B (vị trí 1)
    "3 month": 2,  # YOGA 3T 36B (vị trí 2)
    "6 month": 3,  # YOGA 6T 72B (vị trí 3)
    "1 year": "last()"  # YOGA 12 THÁNG 144B (vị trí cuối cùng)
}


# ... (các hàm khác)

# --- Hàm tự động hóa cho khách cũ (SỬA ĐỔI LẠI BƯỚC 4 - Chọn gói tập theo service_type) ---
def _automate_for_existing_customer_sync(phone_number, service_type, membership_type):
    driver = None
    try:
        driver = _initialize_driver()
        if not driver:
            return {"status": "error", "message": "Không thể khởi tạo trình duyệt cho tự động hóa."}

        if not _login_to_timesoft(driver):
            return {"status": "error", "message": "Đăng nhập Timesoft thất bại."}

        # BƯỚC 1: Tìm khách hàng (Giữ nguyên)
        try:
            radio_all = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "radio_0"))
            )
            radio_all.click()
            time.sleep(1)

            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
            )
            search_input.clear()
            search_input.send_keys(phone_number)
            search_input.send_keys(Keys.ENTER)
            time.sleep(2)
        except TimeoutException as e:
            return {"status": "error", "message": f"Tự động hóa thất bại ở bước tìm khách hàng: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình tìm khách hàng: {e}"}

        # BƯỚC 2: Click vào biểu tượng "Đăng ký gói tập" (dấu cộng) (Giữ nguyên)
        try:
            register_icon = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//a[contains(@ng-click, "showRegisterModal")]//i[@class="fa fa-plus ts-register"]'))
            )
            register_icon.click()
            time.sleep(2)
        except TimeoutException as e:
            return {"status": "error", "message": f"Tự động hóa thất bại ở bước Đăng ký gói tập: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình click Đăng ký gói tập: {e}"}

        # BƯỚC 3: Click vào md-select để mở dropdown "Chọn nhóm dịch vụ" (Giữ nguyên JS click)
        print(f"🏋️‍♀️ Đang mở dropdown 'Chọn nhóm dịch vụ'...")
        try:
            service_group_select_element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[placeholder="Chọn nhóm dịch vụ"]'))
            )
            driver.execute_script("arguments[0].click();", service_group_select_element)

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
            )
            time.sleep(1.5)
        except TimeoutException as e:

            return {"status": "error", "message": f"Tự động hóa thất bại ở bước mở nhóm dịch vụ: {e}"}
        except Exception as e:

            return {"status": "error", "message": f"Lỗi trong quá trình mở nhóm dịch vụ: {e}"}

        # BƯỚC 3b: Chọn nhóm dịch vụ (Gym/Yoga) - SAU KHI DROPDOWN ĐÃ MỞ (Giữ nguyên chọn theo Index)
        print(f"🏋️‍♀️ Đang chọn nhóm dịch vụ: {service_type.upper()}...")
        try:
            target_index_service = -1
            if service_type.lower() == "gym":
                target_index_service = 1
            elif service_type.lower() == "yoga":
                target_index_service = 2

            if target_index_service == -1:

                return {"status": "error",
                        "message": f"Loại dịch vụ '{service_type}' không hợp lệ hoặc không có index được ánh xạ."}

            service_option_element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH,
                                            f'//md-select-menu//md-optgroup[@label="Chọn chức danh"]/md-option[{target_index_service}]'
                                            ))
            )

            try:
                service_option_element.click()

            except ElementClickInterceptedException as e:

                driver.execute_script("arguments[0].click();", service_option_element)


            time.sleep(1)

        except TimeoutException as e:

            return {"status": "error",
                    "message": f"Tự động hóa thất bại ở bước chọn nhóm dịch vụ (Timeout theo index): {e}"}
        except NoSuchElementException as e:

            return {"status": "error", "message": f"Không tìm thấy tùy chọn '{service_type}' theo vị trí đã định: {e}"}
        except Exception as e:

            return {"status": "error", "message": f"Lỗi trong quá trình chọn nhóm dịch vụ theo index: {e}"}

        # BƯỚC 4: Chọn gói tập (SỬA ĐỔI LẠI - CHỌN MAP DỰA TRÊN service_type)

        try:
            product_select = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[ng-model="item.ProductIdStr"]'))
            )
            product_select.click()

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
            )
            time.sleep(1)

            # Chọn map dựa trên service_type
            current_membership_map = None
            if service_type.lower() == "gym":
                current_membership_map = MEMBERSHIP_INDEX_MAP_GYM
            elif service_type.lower() == "yoga":
                current_membership_map = MEMBERSHIP_INDEX_MAP_YOGA
            else:

                return {"status": "error",
                        "message": f"Loại dịch vụ '{service_type}' không hợp lệ hoặc không có map gói tập được định nghĩa."}

            target_index_membership_xpath_part = current_membership_map.get(membership_type)
            if target_index_membership_xpath_part is None:

                return {"status": "error",
                        "message": f"Gói tập '{membership_type}' không hợp lệ hoặc không có index được ánh xạ trong map của {service_type.upper()}."}

            # Xây dựng XPath sử dụng md-optgroup label="Tìm gói"
            membership_option_xpath = (
                f'//md-select-menu//md-optgroup[@label="Tìm gói"]/md-option[{target_index_membership_xpath_part}]'
            )

            membership_option_element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, membership_option_xpath))
            )

            try:
                membership_option_element.click()

            except ElementClickInterceptedException as e:

                driver.execute_script("arguments[0].click();", membership_option_element)


            time.sleep(1)

        except TimeoutException as e:

            return {"status": "error", "message": f"Tự động hóa thất bại ở bước chọn gói tập (Timeout theo index): {e}"}
        except NoSuchElementException as e:

            return {"status": "error",
                    "message": f"Không tìm thấy gói tập '{membership_type}' theo vị trí đã định cho {service_type}: {e}"}
        except Exception as e:

            return {"status": "error", "message": f"Lỗi trong quá trình chọn gói tập theo index: {e}"}

        # BƯỚC 5: Chọn kiểu thanh toán (Giữ nguyên)

        try:
            payment_type_select = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[ng-model="item.PaymentType"]'))
            )
            payment_type_select.click()

            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
            )
            time.sleep(1)

            transfer_option_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                                            '//md-select-menu//md-optgroup[@label="Chọn kiểu thanh toán"]/md-option[2]'
                                            ))
            )
            transfer_option_element.click()

            time.sleep(1)
        except ElementClickInterceptedException as e:

            driver.execute_script("arguments[0].click();", transfer_option_element)

            time.sleep(1)
        except TimeoutException as e:

            return {"status": "error", "message": f"Tự động hóa thất bại ở bước chọn kiểu thanh toán: {e}"}
        except NoSuchElementException as e:

            return {"status": "error", "message": f"Tùy chọn thanh toán 'Chuyển khoản' không tìm thấy: {e}"}
        except Exception as e:

            return {"status": "error", "message": f"Lỗi trong quá trình chọn kiểu thanh toán: {e}"}

        # BƯỚC 6: Chọn tài khoản duy nhất (Giữ nguyên từ lần sửa đổi gần nhất - Dùng Index 1 trong md-optgroup + JS Click)

        try:
            bank_account_select = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[ng-model="item.BankAccountIdStr"]'))
            )
            driver.execute_script("arguments[0].click();", bank_account_select)


            WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
            )
            time.sleep(2)

            bank_account_option_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//md-select-menu//md-optgroup[@label="Chọn tài khoản"]/md-option[1]'
                                                ))
            )

            driver.execute_script("arguments[0].click();", bank_account_option_element)



            time.sleep(1)
        except TimeoutException as e:

            try:
                current_html = driver.page_source
            except Exception as html_err:
                return {"status": "error", "message": f"Tự động hóa thất bại ở bước chọn tài khoản: {e}"}
        except NoSuchElementException as e:

            return {"status": "error", "message": f"Không tìm thấy tùy chọn tài khoản ở vị trí đầu tiên: {e}"}
        except Exception as e:

            return {"status": "error", "message": f"Lỗi trong quá trình chọn tài khoản: {e}"}

        # BƯỚC 7: Bấm nút "Tạo mới" (Tạo gói tập) (Giữ nguyên)

        try:
            create_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "aInsert"))
            )
            create_button.click()

            WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, "aInsert")))

            return {"status": "success", "message": "Gia hạn gói tập thành công.", "final_action": "return_home"}
        except TimeoutException as e:

            return {"status": "error", "message": f"Tự động hóa thất bại ở bước tạo gói tập: {e}"}
        except Exception as e:

            return {"status": "error", "message": f"Lỗi trong quá trình tạo gói tập: {e}"}

    except Exception as e:

        return {"status": "error", "message": f"Lỗi không xác định trong quá trình gia hạn gói tập: {e}"}
    finally:
        if driver:
            driver.quit()


# ... (các hàm _automate_for_new_customer_sync, @app.route, và if __name__ == '__main__': như cũ)




# --- Hàm mô phỏng tự động hóa cho khách mới ---
# LƯU Ý: Phần này vẫn chỉ là mô phỏng. Bạn cần thêm logic Selenium thực tế vào đây.
def _automate_for_new_customer_sync(phone_number, full_name, service_type, membership_type):
    driver = None
    try:
        driver = _initialize_driver()
        if not driver:
            return {"status": "error", "message": "Không thể khởi tạo trình duyệt cho tự động hóa."}

        if not _login_to_timesoft(driver):
            return {"status": "error", "message": "Đăng nhập Timesoft thất bại."}

        print("Đang điều hướng đến trang đăng ký khách hàng mới (giả định)...")
        time.sleep(2) # Đợi trang tải
        try:
            # Sử dụng XPATH để tìm nút dựa trên class và text
            add_new_customer_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'btn-green') and contains(., 'Tạo mới và đăng ký(F1)')]")
                )
            )
            add_new_customer_button.click()
            print("Đã click nút 'Tạo mới và đăng ký (F1)'.")
            time.sleep(2)  # Đợi form thêm mới hiển thị
        except TimeoutException as e:
            return {"status": "error",
                    "message": f"Không tìm thấy hoặc không click được nút 'Tạo mới và đăng ký (F1)': {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi khi click nút 'Tạo mới và đăng ký (F1)': {e}"}
        time.sleep(1)
        try:
            # Tìm trường nhập "Họ và tên" (full_name)
            # Dựa trên HTML bạn cung cấp: ng-model="item.Name"
            full_name_input_selector = (By.XPATH, "//input[@ng-model='item.Name' and @type='text']")
            full_name_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(full_name_input_selector)
            )
            full_name_input.click()  # Click vào trường tên
            print("Đã click vào trường 'Họ và tên'.")
            full_name_input.send_keys(full_name)  # Sau đó mới nhập
            print(f"Đã điền tên: {full_name}")
            time.sleep(1)

            phone_number_input_selector = (By.XPATH, "//input[@ng-model='item.Mobile' and @type='text']")
            phone_number_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(phone_number_input_selector)
            )
            phone_number_input.click()  # Click vào trường số điện thoại (tùy chọn, nhưng nên làm)
            print("Đã click vào trường 'Số điện thoại'.")
            phone_number_input.send_keys(phone_number)
            print(f"Đã điền số điện thoại: {phone_number}")


        except TimeoutException:
            return {"status": "error",
"message": "Không tìm thấy các trường thông tin khách hàng (tên, SĐT) để điền. Vui lòng kiểm tra lại XPath hoặc selector trong code."}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi khi điền thông tin cá nhân: {e}"}

        time.sleep(1)
        print("Đang tìm và click nút 'Tạo mới (F4)' để lưu khách hàng...")
        try:
            # Sử dụng XPATH để tìm nút dựa trên class 'btn-success' và text 'Tạo mới(F4)'
            create_new_customer_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'btn-success') and contains(., 'Tạo mới(F4)')]")
                )
            )
            create_new_customer_button.click()
            print("Đã click nút 'Tạo mới (F4)' để lưu khách hàng mới.")
            time.sleep(2)  # Đợi trang chi tiết tải hoàn tất và các script load
        except TimeoutException as e:
            return {"status": "error",
                    "message": f"Không tìm thấy nút 'Tạo mới (F4)' hoặc quá trình lưu không phản hồi hoặc không chuyển hướng đúng trang: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi khi lưu khách hàng mới: {e}"}
        time.sleep(5)  # Giả lập thời gian xử lý cuối cùng trước khi chuyển hướng

        result_existing_customer = _automate_for_existing_customer_sync(
             phone_number, service_type, membership_type
        )

        if result_existing_customer["status"] == "success":
            print("Cập nhật gói tập sau khi đăng ký khách mới thành công.")
            return {"status": "success",
                    "message": "Đăng kí gói tập mới thành công và đã cập nhật gói tập. Quý khách sẽ được chuyển sang màn hình cập nhật khuôn mặt trong 5 giây",
                    "final_action": "redirect_faceid", "redirect_delay": 5}
        else:
            # Nếu có lỗi khi cập nhật gói tập, trả về lỗi đó
            return {"status": "error",
                    "message": f"Đăng ký khách mới thành công, nhưng lỗi khi cập nhật gói tập: {result_existing_customer['message']}"}


    except Exception as e:
        # Ghi log lỗi chi tiết hơn nếu cần
        print(f"Lỗi không xác định trong quá trình đăng ký mới: {e}")
        return {"status": "error", "message": f"Lỗi trong quá trình đăng ký mới: {e}"}
    finally:
        if driver:
            driver.quit()
# --- Endpoint để bắt đầu tự động hóa ---
@app.route('/start-automation', methods=['POST'])
def start_automation():
    print("[auto_dk.py] Received request for /start-automation")
    try:
        data = request.get_json()
        print("[auto_dk.py] Received data:", data)
        
        if not data:
            print("[auto_dk.py] No data received in request")
            return jsonify({"status": "error", "message": "No data received"}), 400

        # Validate required fields
        required_fields = ['customerType', 'phoneNumber', 'service', 'membership']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"[auto_dk.py] Missing required fields: {missing_fields}")
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Extract data
        customer_type = data['customerType']
        phone_number = data['phoneNumber']
        service_type = data['service']
        membership_type = data['membership']
        full_name = data.get('fullName', '')  # Optional for returning customers

        print(f"[auto_dk.py] Processing request for customer type: {customer_type}")
        print(f"[auto_dk.py] Phone: {phone_number}, Service: {service_type}, Membership: {membership_type}")

        # Process based on customer type
        if customer_type == 'new':
            if not full_name:
                print("[auto_dk.py] Missing fullName for new customer")
                return jsonify({
                    "status": "error",
                    "message": "Full name is required for new customers"
                }), 400
            result = _automate_for_new_customer_sync(phone_number, full_name, service_type, membership_type)
        else:  # returning customer
            result = _automate_for_existing_customer_sync(phone_number, service_type, membership_type)

        print(f"[auto_dk.py] Automation result: {result}")
        return jsonify(result)

    except Exception as e:
        print(f"[auto_dk.py] Error in start_automation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


if __name__ == '__main__':
    print("[auto_dk.py] Starting server on port 5007...")
    app.run(host='0.0.0.0', port=5007, debug=True)
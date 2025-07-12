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
import pyperclip
import signal

app = Flask(__name__)
CORS(app)

# Timeout tổng thể cho toàn bộ quá trình automation (50 giây - tăng cho modal)
TOTAL_TIMEOUT = 50

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Quá trình automation đã vượt quá 35 giây")

# --- CẤU HÌNH SELENIUM ---
def _initialize_driver():
    """Khởi tạo và trả về một instance WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Tối ưu: tắt tải ảnh, font, stylesheet để tăng tốc
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.fonts": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Thêm script để ẩn webdriver
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set timeout tối ưu cho page load
        driver.set_page_load_timeout(8)  # Tối ưu: 8 giây cho đăng nhập nhanh
        driver.implicitly_wait(2)  # Tối ưu: 2 giây cho đăng nhập nhanh
        
        print("✅ Đã khởi tạo trình duyệt thành công")
        return driver
    except WebDriverException as e:
        print(f"❌ Lỗi khởi tạo Chrome driver: {e}")
        return None
    except Exception as e:
        print(f"❌ Lỗi không xác định khi khởi tạo driver: {e}")
        return None

def _login_to_timesoft(driver: webdriver.Chrome):
    """Thực hiện các bước đăng nhập vào Timesoft."""
    try:
        print(f"🔄 Đang đăng nhập...")
        
        driver.get("https://hdfitnessyoga.timesoft.vn/")
        print("✅ Đã truy cập trang web")
        
        # Đợi trang load hoàn toàn (tối ưu: 3 giây)
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Đợi form đăng nhập xuất hiện (tối ưu: 2 giây)
        username_field = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "UserName"))
        )
        password_field = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "Password"))
        )
        
        # Clear và nhập thông tin đăng nhập (tối ưu: không sleep)
        username_field.clear()
        username_field.send_keys("Vuongvv")
        print("✅ Đã nhập username")
        
        password_field.clear()
        password_field.send_keys("291199")
        print("✅ Đã nhập password")
        
        # Click nút đăng nhập (tối ưu: 2 giây)
        login_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.ID, "btnLogin"))
        )
        login_button.click()
        print("✅ Đã click nút đăng nhập")
        
        # Đợi trang chính xuất hiện (tối ưu: 5 giây - quan trọng nhất)
        # Thử nhiều cách để đảm bảo đăng nhập thành công
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "radio_0"))
            )
        except TimeoutException:
            # Thử cách khác nếu radio_0 không xuất hiện
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
                )
            except TimeoutException:
                # Thử cách cuối cùng
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
        
        print("✅ Đăng nhập thành công!")
        return True
        
    except TimeoutException as e:
        print(f"❌ Timeout khi đăng nhập: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định khi đăng nhập: {e}")
        return False


# automation_app.py

# ... (các imports khác)

# Ánh xạ gói tập sang index cho GYM - Phân biệt khách cũ và khách mới
MEMBERSHIP_INDEX_MAP_GYM_EXISTING = {
    "1 year": 2,  # GYM 12 THÁNG (c) khách cũ
    "1 month": 3,  # GYM 1 THÁNG (c) khách cũ
    "1 day": 4,  # GYM 1 NGÀY (c) khách cũ
    "3 months": 5,  # GYM 3 THÁNG (c) khách cũ
    "6 months": 6,  # GYM 6 THÁNG (c) khách cũ
}

MEMBERSHIP_INDEX_MAP_GYM_NEW = {
    "1 year": 10,  # GYM 12 THÁNG (m) khách mới
    "1 month": 7,  # GYM 1 THÁNG (m) khách mới
    "1 day": 11,  # GYM 1 NGÀY (m) khách mới
    "3 months": 8,  # GYM 3 THÁNG (m) khách mới
    "6 months": 9,  # GYM 6 THÁNG (m) khách mới
}

# Ánh xạ gói tập sang index cho YOGA - Phân biệt khách cũ và khách mới
MEMBERSHIP_INDEX_MAP_YOGA_EXISTING = {
    "1 month": 1,  # Yoga 1T 12B (c) khách cũ
    "3 months": 2,  # YOGA 3T 36B (c) khách cũ
    "6 months": 3,  # YOGA 6T 72B (c) khách cũ
    "1 year": "last()"  # YOGA 12 THÁNG 144B (c) khách cũ
}

MEMBERSHIP_INDEX_MAP_YOGA_NEW = {
    "1 month": 12,  # Yoga 1T 12B (m) khách mới
    "3 months": 13,  # YOGA 3T 36B (m) khách mới
    "6 months": 10,  # YOGA 6T 72B (m) khách mới
    "1 year": "11"  # YOGA 12 THÁNG 144B (m) khách mới
}


def _get_membership_map(service_type, customer_type):
    """
    Lấy map gói tập phù hợp dựa trên loại dịch vụ và loại khách hàng
    """
    if service_type.lower() == "gym":
        if customer_type == "new":
            return MEMBERSHIP_INDEX_MAP_GYM_NEW
        else:  # existing
            return MEMBERSHIP_INDEX_MAP_GYM_EXISTING
    elif service_type.lower() == "yoga":
        if customer_type == "new":
            return MEMBERSHIP_INDEX_MAP_YOGA_NEW
        else:  # existing
            return MEMBERSHIP_INDEX_MAP_YOGA_EXISTING
    else:
        return None


def _create_membership_for_customer(phone_number, service_type, membership_type, customer_type):
    """
    Tạo gói tập cho khách hàng với map phù hợp dựa trên loại khách hàng
    """
    driver = None
    start_time = time.time()
    timer = None
    try:
        # Thiết lập timeout tổng thể
        if os.name != 'nt':  # Unix/Linux
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(TOTAL_TIMEOUT)
        else:  # Windows
            def raise_timeout():
                raise TimeoutError(f"Quá trình automation đã vượt quá {TOTAL_TIMEOUT} giây (Windows)")
            timer = threading.Timer(TOTAL_TIMEOUT, raise_timeout)
            timer.start()
        
        print(f"🚀 Bắt đầu tạo gói tập cho khách hàng: {phone_number} (loại: {customer_type})")
        
        driver = _initialize_driver()
        if not driver:
            return {"status": "error", "message": "Không thể khởi tạo trình duyệt cho tự động hóa."}

        if not _login_to_timesoft(driver):
            return {"status": "error", "message": "Đăng nhập Timesoft thất bại."}

        # BƯỚC 1: Tìm khách hàng (Tối ưu timeout)
        try:
            radio_all = WebDriverWait(driver, 4).until(  # Tối ưu: 4 giây
                EC.element_to_be_clickable((By.ID, "radio_0"))
            )
            radio_all.click()
            time.sleep(0.3)  # Tối ưu: 0.3 giây

            search_input = WebDriverWait(driver, 4).until(  # Tối ưu: 4 giây
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
            )
            search_input.clear()
            search_input.send_keys(phone_number)
            search_input.send_keys(Keys.ENTER)
            time.sleep(1)  # Tối ưu: 0.8 giây - đủ để load kết quả
        except TimeoutException as e:
            return {"status": "error", "message": f"Tự động hóa thất bại ở bước tìm khách hàng: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình tìm khách hàng: {e}"}

        # BƯỚC 2: Click vào biểu tượng "Đăng ký gói tập" (Tăng timeout cho modal)
        try:
            # Thử nhiều cách khác nhau để tìm nút đăng ký gói tập
            register_icon = None
            
            # Cách 1: Tìm theo XPath với class và ng-click (tăng: 8 giây)
            try:
                register_icon = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//a[contains(@ng-click, "showRegisterModal")]//i[@class="fa fa-plus ts-register"]'))
                )
            except TimeoutException:
                print("Cách 1 thất bại, thử cách 2...")
                
                # Cách 2: Tìm theo class name (tăng: 4 giây)
                try:
                    register_icon = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "ts-register"))
                    )
                except TimeoutException:
                    print("Cách 2 thất bại, thử cách 3...")
                    
                    # Cách 3: Tìm theo text content (tăng: 4 giây)
                    try:
                        register_icon = WebDriverWait(driver, 4).until(
                            EC.element_to_be_clickable((By.XPATH, "//i[contains(@class, 'fa-plus')]"))
                        )
                    except TimeoutException:
                        print("Cách 3 thất bại, thử cách 4...")
                        
                        # Cách 4: Tìm theo link text (tăng: 4 giây)
                        try:
                            register_icon = WebDriverWait(driver, 4).until(
                                EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Đăng ký') or contains(., 'Register')]") )
                            )
                        except TimeoutException:
                            # Nếu tất cả cách đều thất bại, lấy HTML để debug
                            current_html = driver.page_source
                            print(f"Không tìm thấy nút đăng ký gói tập. HTML hiện tại (cắt 800 ký tự): {current_html[:800]}")
                            return {"status": "error", "message": "Không tìm thấy nút đăng ký gói tập. Vui lòng kiểm tra lại trang web hoặc liên hệ hỗ trợ."}
            
            if register_icon:
                for attempt in range(3):
                    try:
                        try:
                            register_icon.click()
                        except ElementClickInterceptedException:
                            driver.execute_script("arguments[0].click();", register_icon)
                        time.sleep(1.2)
                        # Kiểm tra modal đã mở chưa bằng JS
                        modal_open = driver.execute_script('''
                            var el = document.querySelector('md-select[placeholder="Chọn nhóm dịch vụ"]');
                            return el && el.offsetParent !== null;
                        ''')
                        if modal_open:
                            break
                    except Exception as e:
                        print(f"Thử mở modal lần {attempt+1} thất bại: {e}")
                    if attempt == 2:
                        current_html = driver.page_source
                        print(f"Không mở được modal sau 3 lần thử. HTML hiện tại (cắt 800 ký tự): {current_html[:800]}")
                        return {"status": "error", "message": "Đã thử nhiều lần nhưng modal không mở. Vui lòng thử lại."}
                else:
                    # Nếu sau 3 lần vẫn chưa mở, trả về lỗi
                    return {"status": "error", "message": "Không mở được modal đăng ký gói tập sau nhiều lần thử."}
                # Kiểm tra xem modal đã mở chưa (tăng: 8 giây)
                try:
                    WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'md-select[placeholder="Chọn nhóm dịch vụ"]'))
                    )
                except TimeoutException:
                    return {"status": "error", "message": "Đã click nút đăng ký gói tập nhưng modal không mở. Vui lòng thử lại."}
        
        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình click Đăng ký gói tập: {str(e)}"}

        # BƯỚC 3: Click vào md-select để mở dropdown "Chọn nhóm dịch vụ" (Tăng timeout)
        print(f"🏋️‍♀️ Đang mở dropdown 'Chọn nhóm dịch vụ'...")
        try:
            service_group_select_element = None
            
            # Cách 1: Tìm theo placeholder (tăng: 6 giây)
            try:
                service_group_select_element = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[placeholder="Chọn nhóm dịch vụ"]'))
                )
            except TimeoutException:
                print("Cách 1 thất bại, thử cách 2...")
                
                # Cách 2: Tìm theo ng-model (tăng: 4 giây)
                try:
                    service_group_select_element = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[ng-model*="Service"]'))
                    )
                except TimeoutException:
                    print("Cách 2 thất bại, thử cách 3...")
                    
                    # Cách 3: Tìm tất cả md-select và chọn cái đầu tiên
                    try:
                        all_md_selects = driver.find_elements(By.CSS_SELECTOR, 'md-select')
                        if all_md_selects:
                            service_group_select_element = all_md_selects[0]
                            print(f"Tìm thấy {len(all_md_selects)} md-select elements, sử dụng cái đầu tiên")
                        else:
                            raise Exception("Không tìm thấy md-select nào")
                    except Exception as e:
                        current_html = driver.page_source
                        print(f"Không tìm thấy dropdown chọn nhóm dịch vụ. HTML hiện tại (cắt 800 ký tự): {current_html[:800]}")
                        return {"status": "error", "message": "Không tìm thấy dropdown chọn nhóm dịch vụ. Vui lòng kiểm tra lại trang web."}
            
            if service_group_select_element:
                # Thử click bình thường trước
                try:
                    service_group_select_element.click()
                except ElementClickInterceptedException:
                    # Nếu bị chặn, dùng JavaScript click
                    driver.execute_script("arguments[0].click();", service_group_select_element)

                # Đợi dropdown mở (tăng: 5 giây)
                try:
                    WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                    )
                    time.sleep(0.5)  # Tăng: 0.5 giây - đủ để dropdown ổn định
                except TimeoutException:
                    return {"status": "error", "message": "Đã click dropdown nhưng menu không mở. Vui lòng thử lại."}
                    
        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình mở nhóm dịch vụ: {str(e)}"}

        # Kiểm tra thời gian đã trôi qua
        elapsed_time = time.time() - start_time
        if elapsed_time > 45:  # Tăng: 45 giây - phù hợp với timeout mới cho modal
            return {"status": "error", "message": f"Quá trình automation đã mất quá nhiều thời gian ({elapsed_time:.1f}s). Vui lòng thử lại."}

        # BƯỚC 3b: Chọn nhóm dịch vụ (Gym/Yoga) - Cải thiện error handling
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

            service_option_element = None
            
            # Cách 1: Tìm theo XPath với optgroup label
            try:
                service_option_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                f'//md-select-menu//md-optgroup[@label="Chọn chức danh"]/md-option[{target_index_service}]'
                                                ))
                )
            except TimeoutException:
                print("Cách 1 thất bại, thử cách 2...")
                
                # Cách 2: Tìm theo text content
                try:
                    if service_type.lower() == "gym":
                        service_option_element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//md-option[contains(text(), 'GYM') or contains(text(), 'Gym')]"))
                        )
                    elif service_type.lower() == "yoga":
                        service_option_element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//md-option[contains(text(), 'YOGA') or contains(text(), 'Yoga')]"))
                        )
                except TimeoutException:
                    print("Cách 2 thất bại, thử cách 3...")
                    
                    # Cách 3: Tìm tất cả options và chọn theo index
                    try:
                        all_options = driver.find_elements(By.CSS_SELECTOR, 'md-select-menu md-option')
                        if len(all_options) >= target_index_service:
                            service_option_element = all_options[target_index_service - 1]
                            print(f"Tìm thấy {len(all_options)} options, chọn option thứ {target_index_service}")
                        else:
                            raise Exception(f"Chỉ có {len(all_options)} options, không đủ để chọn option thứ {target_index_service}")
                    except Exception as e:
                        current_html = driver.page_source
                        print(f"Không tìm thấy option cho {service_type}. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                        return {"status": "error", 
                                "message": f"Không tìm thấy tùy chọn '{service_type}' trong dropdown. Vui lòng kiểm tra lại."}

            if service_option_element:
                # Thử click bình thường trước
                try:
                    service_option_element.click()
                except ElementClickInterceptedException:
                    # Nếu bị chặn, dùng JavaScript click
                    driver.execute_script("arguments[0].click();", service_option_element)

                time.sleep(1)
                
                # Kiểm tra xem option đã được chọn chưa
                try:
                    WebDriverWait(driver, 5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                    )
                except TimeoutException:
                    return {"status": "error", "message": f"Đã click option {service_type} nhưng dropdown không đóng. Vui lòng thử lại."}

        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình chọn nhóm dịch vụ: {str(e)}"}

        # BƯỚC 4: Chọn gói tập - Cải thiện error handling với map phù hợp
        print(f"🏋️‍♀️ Đang chọn gói tập: {membership_type}...")
        try:
            product_select = None
            
            # Cách 1: Tìm theo ng-model
            try:
                product_select = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[ng-model="item.ProductIdStr"]'))
                )
            except TimeoutException:
                print("Cách 1 thất bại, thử cách 2...")
                
                # Cách 2: Tìm theo placeholder
                try:
                    product_select = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[placeholder*="gói"]'))
                    )
                except TimeoutException:
                    print("Cách 2 thất bại, thử cách 3...")
                    
                    # Cách 3: Tìm tất cả md-select và chọn cái thứ 2 (sau service group)
                    try:
                        all_md_selects = driver.find_elements(By.CSS_SELECTOR, 'md-select')
                        if len(all_md_selects) >= 2:
                            product_select = all_md_selects[1]
                            print(f"Tìm thấy {len(all_md_selects)} md-select elements, sử dụng cái thứ 2")
                        else:
                            raise Exception(f"Chỉ có {len(all_md_selects)} md-select elements, không đủ để chọn cái thứ 2")
                    except Exception as e:
                        current_html = driver.page_source
                        print(f"Không tìm thấy dropdown chọn gói tập. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                        return {"status": "error", "message": "Không tìm thấy dropdown chọn gói tập. Vui lòng kiểm tra lại trang web."}
            
            if product_select:
                # Click để mở dropdown
                try:
                    product_select.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", product_select)

                # Đợi dropdown mở
                try:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                    )
                    time.sleep(1)
                except TimeoutException:
                    return {"status": "error", "message": "Đã click dropdown gói tập nhưng menu không mở. Vui lòng thử lại."}

                # Chọn map dựa trên service_type và customer_type
                current_membership_map = _get_membership_map(service_type, customer_type)
                if current_membership_map is None:
                    return {"status": "error",
                            "message": f"Loại dịch vụ '{service_type}' không hợp lệ hoặc không có map gói tập được định nghĩa."}

                target_index_membership_xpath_part = current_membership_map.get(membership_type)
                if target_index_membership_xpath_part is None:
                    return {"status": "error",
                            "message": f"Gói tập '{membership_type}' không hợp lệ hoặc không có index được ánh xạ trong map của {service_type.upper()} cho khách {customer_type}."}

                # Tìm và chọn gói tập
                membership_option_element = None
                
                # Cách 1: Tìm theo XPath với optgroup label
                try:
                    membership_option_xpath = (
                        f'//md-select-menu//md-optgroup[@label="Tìm gói"]/md-option[{target_index_membership_xpath_part}]'
                    )
                    membership_option_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, membership_option_xpath))
                    )
                except TimeoutException:
                    print("Cách 1 thất bại, thử cách 2...")
                    
                    # Cách 2: Tìm theo text content
                    try:
                        membership_option_element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//md-option[contains(text(), '{membership_type}')]"))
                        )
                    except TimeoutException:
                        print("Cách 2 thất bại, thử cách 3...")
                        
                        # Cách 3: Tìm tất cả options và chọn theo index
                        try:
                            all_membership_options = driver.find_elements(By.CSS_SELECTOR, 'md-select-menu md-option')
                            if len(all_membership_options) >= target_index_membership_xpath_part:
                                membership_option_element = all_membership_options[target_index_membership_xpath_part - 1]
                                print(f"Tìm thấy {len(all_membership_options)} membership options, chọn option thứ {target_index_membership_xpath_part}")
                            else:
                                raise Exception(f"Chỉ có {len(all_membership_options)} membership options, không đủ để chọn option thứ {target_index_membership_xpath_part}")
                        except Exception as e:
                            current_html = driver.page_source
                            print(f"Không tìm thấy gói tập {membership_type}. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                            return {"status": "error",
                                    "message": f"Không tìm thấy gói tập '{membership_type}' trong dropdown. Vui lòng kiểm tra lại."}

                if membership_option_element:
                    # Click để chọn gói tập
                    try:
                        membership_option_element.click()
                    except ElementClickInterceptedException:
                        driver.execute_script("arguments[0].click();", membership_option_element)

                    time.sleep(1)
                    
                    # Kiểm tra xem gói tập đã được chọn chưa
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                        )
                    except TimeoutException:
                        return {"status": "error", "message": f"Đã click gói tập {membership_type} nhưng dropdown không đóng. Vui lòng thử lại."}

        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình chọn gói tập: {str(e)}"}

        # BƯỚC 5: Chọn kiểu thanh toán - Cải thiện error handling
        print("🏋️‍♀️ Đang chọn kiểu thanh toán...")
        try:
            payment_type_select = None
            
            # Cách 1: Tìm theo ng-model
            try:
                payment_type_select = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[ng-model="item.PaymentType"]'))
                )
            except TimeoutException:
                print("Cách 1 thất bại, thử cách 2...")
                
                # Cách 2: Tìm theo placeholder
                try:
                    payment_type_select = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[placeholder*="thanh toán"]'))
                    )
                except TimeoutException:
                    print("Cách 2 thất bại, thử cách 3...")
                    
                    # Cách 3: Tìm tất cả md-select và chọn cái thứ 3 (sau service group và product)
                    try:
                        all_md_selects = driver.find_elements(By.CSS_SELECTOR, 'md-select')
                        if len(all_md_selects) >= 3:
                            payment_type_select = all_md_selects[2]
                            print(f"Tìm thấy {len(all_md_selects)} md-select elements, sử dụng cái thứ 3")
                        else:
                            raise Exception(f"Chỉ có {len(all_md_selects)} md-select elements, không đủ để chọn cái thứ 3")
                    except Exception as e:
                        current_html = driver.page_source
                        print(f"Không tìm thấy dropdown chọn kiểu thanh toán. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                        return {"status": "error", "message": "Không tìm thấy dropdown chọn kiểu thanh toán. Vui lòng kiểm tra lại trang web."}
            
            if payment_type_select:
                # Click để mở dropdown
                try:
                    payment_type_select.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", payment_type_select)

                # Đợi dropdown mở
                try:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                    )
                    time.sleep(1)
                except TimeoutException:
                    return {"status": "error", "message": "Đã click dropdown kiểu thanh toán nhưng menu không mở. Vui lòng thử lại."}

                # Chọn tùy chọn "Chuyển khoản"
                transfer_option_element = None
                
                # Cách 1: Tìm theo XPath với optgroup label
                try:
                    transfer_option_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH,
                                                    '//md-select-menu//md-optgroup[@label="Chọn kiểu thanh toán"]/md-option[2]'
                                                    ))
                    )
                except TimeoutException:
                    print("Cách 1 thất bại, thử cách 2...")
                    
                    # Cách 2: Tìm theo text content
                    try:
                        transfer_option_element = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//md-option[contains(text(), 'Chuyển khoản') or contains(text(), 'Transfer')]"))
                        )
                    except TimeoutException:
                        print("Cách 2 thất bại, thử cách 3...")
                        
                        # Cách 3: Tìm tất cả options và chọn cái thứ 2
                        try:
                            all_payment_options = driver.find_elements(By.CSS_SELECTOR, 'md-select-menu md-option')
                            if len(all_payment_options) >= 2:
                                transfer_option_element = all_payment_options[1]
                                print(f"Tìm thấy {len(all_payment_options)} payment options, chọn option thứ 2")
                            else:
                                raise Exception(f"Chỉ có {len(all_payment_options)} payment options, không đủ để chọn option thứ 2")
                        except Exception as e:
                            current_html = driver.page_source
                            print(f"Không tìm thấy tùy chọn chuyển khoản. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                            return {"status": "error", "message": "Không tìm thấy tùy chọn 'Chuyển khoản' trong dropdown. Vui lòng kiểm tra lại."}

                if transfer_option_element:
                    # Click để chọn kiểu thanh toán
                    try:
                        transfer_option_element.click()
                    except ElementClickInterceptedException:
                        driver.execute_script("arguments[0].click();", transfer_option_element)

                    time.sleep(1)
                    
                    # Kiểm tra xem option đã được chọn chưa
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                        )
                    except TimeoutException:
                        return {"status": "error", "message": "Đã click tùy chọn chuyển khoản nhưng dropdown không đóng. Vui lòng thử lại."}

        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình chọn kiểu thanh toán: {str(e)}"}

        # BƯỚC 6: Chọn tài khoản - Cải thiện error handling
        print("🏋️‍♀️ Đang chọn tài khoản...")
        try:
            bank_account_select = None
            
            # Cách 1: Tìm theo ng-model
            try:
                bank_account_select = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[ng-model="item.BankAccountIdStr"]'))
                )
            except TimeoutException:
                print("Cách 1 thất bại, thử cách 2...")
                
                # Cách 2: Tìm theo placeholder
                try:
                    bank_account_select = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'md-select[placeholder*="tài khoản"]'))
                    )
                except TimeoutException:
                    print("Cách 2 thất bại, thử cách 3...")
                    
                    # Cách 3: Tìm tất cả md-select và chọn cái cuối cùng
                    try:
                        all_md_selects = driver.find_elements(By.CSS_SELECTOR, 'md-select')
                        if all_md_selects:
                            bank_account_select = all_md_selects[-1]
                            print(f"Tìm thấy {len(all_md_selects)} md-select elements, sử dụng cái cuối cùng")
                        else:
                            raise Exception("Không tìm thấy md-select nào")
                    except Exception as e:
                        current_html = driver.page_source
                        print(f"Không tìm thấy dropdown chọn tài khoản. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                        return {"status": "error", "message": "Không tìm thấy dropdown chọn tài khoản. Vui lòng kiểm tra lại trang web."}
            
            if bank_account_select:
                # Click để mở dropdown
                try:
                    bank_account_select.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", bank_account_select)

                # Đợi dropdown mở
                try:
                    WebDriverWait(driver, 15).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                    )
                    time.sleep(2)
                except TimeoutException:
                    return {"status": "error", "message": "Đã click dropdown tài khoản nhưng menu không mở. Vui lòng thử lại."}

                # Chọn tài khoản đầu tiên
                bank_account_option_element = None
                
                # Cách 1: Tìm theo XPath với optgroup label
                try:
                    bank_account_option_element = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH,
                                                        '//md-select-menu//md-optgroup[@label="Chọn tài khoản"]/md-option[1]'
                                                        ))
                    )
                except TimeoutException:
                    print("Cách 1 thất bại, thử cách 2...")
                    
                    # Cách 2: Tìm tất cả options và chọn cái đầu tiên
                    try:
                        all_bank_options = driver.find_elements(By.CSS_SELECTOR, 'md-select-menu md-option')
                        if all_bank_options:
                            bank_account_option_element = all_bank_options[0]
                            print(f"Tìm thấy {len(all_bank_options)} bank account options, chọn option đầu tiên")
                        else:
                            raise Exception("Không tìm thấy tùy chọn tài khoản nào")
                    except Exception as e:
                        current_html = driver.page_source
                        print(f"Không tìm thấy tùy chọn tài khoản. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                        return {"status": "error", "message": "Không tìm thấy tùy chọn tài khoản trong dropdown. Vui lòng kiểm tra lại."}

                if bank_account_option_element:
                    # Click để chọn tài khoản
                    try:
                        bank_account_option_element.click()
                    except ElementClickInterceptedException:
                        driver.execute_script("arguments[0].click();", bank_account_option_element)

                    time.sleep(1)
                    
                    # Kiểm tra xem option đã được chọn chưa
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, '.md-select-menu-container[aria-hidden="false"]'))
                        )
                    except TimeoutException:
                        return {"status": "error", "message": "Đã click tùy chọn tài khoản nhưng dropdown không đóng. Vui lòng thử lại."}

        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình chọn tài khoản: {str(e)}"}

        # BƯỚC 7: Bấm nút "Tạo mới" (Tạo gói tập) - Cải thiện error handling
        print("🏋️‍♀️ Đang tạo gói tập...")
        try:
            create_button = None
            
            # Cách 1: Tìm theo ID
            try:
                create_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "aInsert"))
                )
            except TimeoutException:
                print("Cách 1 thất bại, thử cách 2...")
                
                # Cách 2: Tìm theo text content
                try:
                    create_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tạo mới') or contains(text(), 'Create')]"))
                    )
                except TimeoutException:
                    print("Cách 2 thất bại, thử cách 3...")
                    
                    # Cách 3: Tìm theo class
                    try:
                        create_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.btn-success'))
                        )
                    except TimeoutException:
                        current_html = driver.page_source
                        print(f"Không tìm thấy nút tạo mới. HTML hiện tại (cắt 2000 ký tự): {current_html[:2000]}")
                        return {"status": "error", "message": "Không tìm thấy nút tạo mới. Vui lòng kiểm tra lại trang web."}
            
            if create_button:
                # Click để tạo gói tập
                try:
                    create_button.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", create_button)

                # Đợi nút biến mất (dấu hiệu đang xử lý)
                try:
                    WebDriverWait(driver, 15).until(EC.invisibility_of_element_located((By.ID, "aInsert")))
                    print("✅ Gói tập đã được tạo thành công!")
                    return {"status": "success", "message": "Gia hạn gói tập thành công.", "final_action": "return_home"}
                except TimeoutException:
                    return {"status": "error", "message": "Đã click nút tạo mới nhưng quá trình xử lý không hoàn tất. Vui lòng thử lại."}

        except Exception as e:
            return {"status": "error", "message": f"Lỗi trong quá trình tạo gói tập: {str(e)}"}

    except Exception as e:
        print(f"❌ Lỗi không xác định trong quá trình gia hạn gói tập: {str(e)}")
        # Lấy HTML để debug
        try:
            current_html = driver.page_source
            print(f"HTML hiện tại khi lỗi (cắt 1500 ký tự): {current_html[:1500]}")
        except Exception as html_err:
            print(f"Không thể lấy HTML để debug: {html_err}")
        return {"status": "error", "message": f"Lỗi không xác định trong quá trình gia hạn gói tập: {str(e)}"}
    except TimeoutError:
        elapsed_time = time.time() - start_time
        print(f"⏰ Timeout tổng thể: Quá trình automation đã vượt quá {TOTAL_TIMEOUT} giây (thực tế: {elapsed_time:.1f}s)")
        return {"status": "error", "message": f"Quá trình automation đã vượt quá {TOTAL_TIMEOUT} giây. Vui lòng thử lại."}
    finally:
        # Hủy timeout
        if os.name != 'nt':
            signal.alarm(0)
        elif timer:
            timer.cancel()
        
        if driver:
            try:
                driver.quit()
                print("🔒 Đã đóng trình duyệt")
            except Exception as quit_err:
                print(f"Lỗi khi đóng trình duyệt: {quit_err}")
        
        # In thời gian tổng thể
        total_elapsed = time.time() - start_time
        print(f"⏱️ Tổng thời gian automation: {total_elapsed:.1f} giây")
        if total_elapsed < 20:
            print("🚀 Tốc độ xuất sắc!")
        elif total_elapsed < 30:
            print("⚡ Tốc độ tốt!")
        else:
            print("🐌 Tốc độ chậm, cần tối ưu thêm")


# --- Hàm tự động hóa cho khách cũ (Tối ưu cho 60 giây) ---
def _automate_for_existing_customer_sync(phone_number, service_type, membership_type):
    """
    Hàm wrapper cho khách cũ - gọi hàm chung với customer_type = "existing"
    """
    return _create_membership_for_customer(phone_number, service_type, membership_type, "existing")


# --- Hàm tự động hóa cho khách mới (Tối ưu cho 60 giây) ---
def _automate_for_new_customer_sync(phone_number, full_name, service_type, membership_type):
    driver = None
    start_time = time.time()
    timer = None
    try:
        # Thiết lập timeout tổng thể
        if os.name != 'nt':  # Unix/Linux
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(TOTAL_TIMEOUT)
        else:  # Windows
            def raise_timeout():
                raise TimeoutError(f"Quá trình automation đã vượt quá {TOTAL_TIMEOUT} giây (Windows)")
            timer = threading.Timer(TOTAL_TIMEOUT, raise_timeout)
            timer.start()
        
        print(f"🚀 Bắt đầu automation cho khách hàng mới: {full_name} - {phone_number}")
        
        driver = _initialize_driver()
        if not driver:
            return {"status": "error", "message": "Không thể khởi tạo trình duyệt cho tự động hóa."}

        if not _login_to_timesoft(driver):
            return {"status": "error", "message": "Đăng nhập Timesoft thất bại."}

        print("Đang điều hướng đến trang đăng ký khách hàng mới...")
        time.sleep(0.5)  # Tối ưu: 0.5 giây
        
        try:
            # Sử dụng XPATH để tìm nút dựa trên class và text
            add_new_customer_button = WebDriverWait(driver, 6).until(  # Tối ưu: 6 giây
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'btn-green') and contains(., 'Tạo mới và đăng ký(F1)')]")
                )
            )
            add_new_customer_button.click()
            print("Đã click nút 'Tạo mới và đăng ký (F1)'.")
            time.sleep(0.6)  # Tối ưu: 0.6 giây
        except TimeoutException as e:
            return {"status": "error",
                    "message": f"Không tìm thấy hoặc không click được nút 'Tạo mới và đăng ký (F1)': {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi khi click nút 'Tạo mới và đăng ký (F1)': {e}"}
        
        time.sleep(0.3)  # Tối ưu: 0.3 giây
        
        try:
            # Tìm trường nhập "Họ và tên" (full_name)
            full_name_input_selector = (By.XPATH, "//input[@ng-model='item.Name' and @type='text']")
            full_name_input = WebDriverWait(driver, 4).until(  # Tối ưu: 4 giây
                EC.presence_of_element_located(full_name_input_selector)
            )
            full_name_input.click()
            print("Đã click vào trường 'Họ và tên'.")
            full_name_input.send_keys(full_name)
            print(f"Đã điền tên: {full_name}")
            time.sleep(0.5)  # Tối ưu: 0.5 giây

            phone_number_input_selector = (By.XPATH, "//input[@ng-model='item.Mobile' and @type='text']")
            phone_number_input = WebDriverWait(driver, 4).until(  # Tối ưu: 4 giây
                EC.presence_of_element_located(phone_number_input_selector)
            )
            phone_number_input.click()
            print("Đã click vào trường 'Số điện thoại'.")
            phone_number_input.send_keys(phone_number)
            print(f"Đã điền số điện thoại: {phone_number}")

        except TimeoutException:
            return {"status": "error",
"message": "Không tìm thấy các trường thông tin khách hàng (tên, SĐT) để điền. Vui lòng kiểm tra lại XPath hoặc selector trong code."}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi khi điền thông tin cá nhân: {e}"}

        time.sleep(0.5)  # Tối ưu: 0.5 giây
        
        print("Đang tìm và click nút 'Tạo mới (F4)' để lưu khách hàng...")
        try:
            # Sử dụng XPATH để tìm nút dựa trên class 'btn-success' và text 'Tạo mới(F4)'
            create_new_customer_button = WebDriverWait(driver, 6).until(  # Tối ưu: 6 giây
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class, 'btn-success') and contains(., 'Tạo mới(F4)')]")
                )
            )
            create_new_customer_button.click()
            print("Đã click nút 'Tạo mới (F4)' để lưu khách hàng mới.")
            time.sleep(2)  # Tối ưu: 2 giây - đủ để lưu và chuyển trang
        except TimeoutException as e:
            return {"status": "error",
                    "message": f"Không tìm thấy nút 'Tạo mới (F4)' hoặc quá trình lưu không phản hồi hoặc không chuyển hướng đúng trang: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Lỗi khi lưu khách hàng mới: {e}"}
        
        time.sleep(1.5)  # Tối ưu: 1.5 giây - đủ để trang load

        # Kiểm tra thời gian đã trôi qua trước khi gọi hàm cập nhật gói tập
        elapsed_time = time.time() - start_time
        if elapsed_time > 18:  # Nếu đã dùng hơn 18 giây, dừng lại (giảm từ 25)
            return {"status": "error", "message": f"Quá trình đăng ký khách mới đã mất quá nhiều thời gian ({elapsed_time:.1f}s). Vui lòng thử lại."}

        # Đóng driver trước khi chuyển sang tạo gói cho khách (mở session mới)
        if driver:
            driver.quit()
            driver = None

        # Thêm delay để chờ Timesoft cập nhật khách mới
        time.sleep(2)

        # Tạo gói tập cho khách mới với map phù hợp
        result_existing_customer = _create_membership_for_customer(
             phone_number, service_type, membership_type, "new"
        )

        if result_existing_customer["status"] == "success":
            print("Cập nhật gói tập sau khi đăng ký khách mới thành công.")
            return {"status": "success",
                    "message": "Đăng kí gói tập mới thành công và đã cập nhật gói tập. Quý khách sẽ được chuyển sang màn hình cập nhật khuôn mặt trong 5 giây",
                    "final_action": "redirect_faceid", "redirect_delay": 5}
        else:
            # In log chi tiết nếu có lỗi khi cập nhật gói tập
            print(f"[auto_dk.py] Lỗi khi cập nhật gói tập cho khách mới: {result_existing_customer['message']}")
            return {"status": "error",
                    "message": f"Đăng ký khách mới thành công, nhưng lỗi khi cập nhật gói tập: {result_existing_customer['message']}"}

    except TimeoutError:
        elapsed_time = time.time() - start_time
        print(f"⏰ Timeout tổng thể: Quá trình automation cho khách mới đã vượt quá {TOTAL_TIMEOUT} giây (thực tế: {elapsed_time:.1f}s)")
        return {"status": "error", "message": f"Quá trình automation đã vượt quá {TOTAL_TIMEOUT} giây. Vui lòng thử lại."}
    except Exception as e:
        # Ghi log lỗi chi tiết hơn nếu cần
        print(f"Lỗi không xác định trong quá trình đăng ký mới: {e}")
        return {"status": "error", "message": f"Lỗi trong quá trình đăng ký mới: {e}"}
    finally:
        # Hủy timeout
        if os.name != 'nt':
            signal.alarm(0)
        elif timer:
            timer.cancel()
        
        # Chỉ quit nếu driver vẫn còn (chưa quit ở trên)
        if driver:
            driver.quit()
        
        # In thời gian tổng thể
        total_elapsed = time.time() - start_time
        print(f"⏱️ Tổng thời gian automation cho khách mới: {total_elapsed:.1f} giây")
        if total_elapsed < 18:
            print("🚀 Tốc độ xuất sắc cho khách mới!")
        elif total_elapsed < 25:
            print("⚡ Tốc độ tốt cho khách mới!")
        else:
            print("🐌 Tốc độ chậm cho khách mới, cần tối ưu thêm")


# --- Endpoint để bắt đầu tự động hóa ---
@app.route('/start-automation', methods=['POST'])
def start_automation():
    print("[auto_dk.py] Received request for /start-automation")
    start_time = time.time()
    
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
        
        # In thời gian xử lý
        processing_time = time.time() - start_time
        print(f"[auto_dk.py] Total processing time: {processing_time:.1f} seconds")
        
        return jsonify(result)

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"[auto_dk.py] Error in start_automation after {processing_time:.1f}s: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An error occurred after {processing_time:.1f}s: {str(e)}"
        }), 500


if __name__ == '__main__':
    print("[auto_dk.py] Starting server on port 5007...")
    app.run(host='0.0.0.0', port=5007, debug=True)
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
import tempfile
import shutil
import threading
import uuid
from datetime import datetime
import os
import subprocess

app = Flask(__name__)
CORS(app)

# Lưu trữ trạng thái và kết quả của các task
task_status = {}
task_results = {}

# Giới hạn số Chrome đồng thời
MAX_CHROME_INSTANCES = 2
chrome_semaphore = threading.Semaphore(MAX_CHROME_INSTANCES)

def process_check_phone_task(task_id, phone_number):
    """Hàm xử lý việc kiểm tra thông tin trong background thread"""
    try:
        task_status[task_id] = "processing"
        with chrome_semaphore:
            # Log thông tin môi trường
            try:
                user = os.getlogin()
            except Exception:
                user = os.environ.get("USER", "unknown")
            chrome_version = subprocess.getoutput("google-chrome --version")
            chromedriver_version = subprocess.getoutput("chromedriver --version")
            process_count = subprocess.getoutput("ps aux | wc -l")
            log_info = f"[DEBUG] User: {user}, Chrome: {chrome_version}, Chromedriver: {chromedriver_version}, Process count: {process_count}"
            print(log_info)
            # Có thể lưu log_info vào task_results[task_id] nếu muốn trả về cho client

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--remote-debugging-port=9222")
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
            except Exception as e:
                error_message = f"Could not start Chrome: {type(e).__name__} - {str(e)} | {log_info}"
                task_results[task_id] = {"error": error_message}
                task_status[task_id] = "error"
                return
            try:
                driver.get("https://hdfitnessyoga.timesoft.vn/")
                
                # Đăng nhập
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("Vuongvv")
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "Password"))).send_keys("291199")
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()
                
                # Đợi trang load sau khi đăng nhập
                time.sleep(3)

                # Đợi overlay loading biến mất trước khi click radio
                WebDriverWait(driver, 20).until(
                    EC.invisibility_of_element_located((By.ID, "loading-pane"))
                )
                # Đợi radio_all xuất hiện và click
                radio_all = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "radio_0"))
                )
                radio_all.click()
                time.sleep(1)  # Đợi radio được chọn

                # Đợi input search xuất hiện
                search_input = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
                )
                search_input.clear()
                search_input.send_keys(phone_number)
                search_input.send_keys(Keys.ENTER)

                # Đợi kết quả tìm kiếm load
                time.sleep(3)

                # Đợi bảng kết quả xuất hiện
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.show-table-ready"))
                    )
                    # Đợi thêm 1 giây để đảm bảo dữ liệu load đầy đủ
                    time.sleep(3)
                    
                    html_content = driver.page_source
                    soup = BeautifulSoup(html_content, "html.parser")
                    table_body = soup.find("tbody", class_="show-table-ready")
                    rows = table_body.find_all("tr") if table_body else []
                    data_list = []
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) < 7:
                            continue
                        name_elem = cols[0].find("span", class_="ng-binding")
                        name = name_elem.text.strip() if name_elem else ""
                        phone_text = cols[2].text.strip()
                        service_text = cols[3].text.strip()
                        remaining = ""
                        span_list = cols[5].find_all("span")
                        if span_list:
                            remaining = span_list[0].text.strip()
                        start_date = cols[6].text.strip()
                        end_date = cols[7].text.strip()
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
                    task_results[task_id] = {"results": data_list}
                    task_status[task_id] = "completed"
                except Exception as e:
                    try:
                        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                            (By.XPATH, "//td[@colspan='12' and contains(text(), 'Không tìm thấy bản ghi nào')]")))
                        task_results[task_id] = {"results": []}
                        task_status[task_id] = "completed"
                    except Exception as e2:
                        error_message = f"Error in check_phone (table/result): {type(e).__name__} - {str(e)} | {type(e2).__name__} - {str(e2)}"
                        task_results[task_id] = {"error": error_message}
                        task_status[task_id] = "error"
            except Exception as e:
                error_message = f"Error during driver operation: {type(e).__name__} - {str(e)} | {log_info}"
                task_results[task_id] = {"error": error_message}
                task_status[task_id] = "error"
            finally:
                if driver:
                    driver.quit()
    except Exception as e:
        task_results[task_id] = {"error": str(e)}
        task_status[task_id] = "error"

@app.route("/check-phone", methods=["POST"])
def check_phone():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input, JSON object expected"}), 400
    phone_number = data.get("phone", "")
    
    if not phone_number or len(phone_number) != 10 or not phone_number.isdigit():
        return jsonify({"error": "Invalid phone number"}), 400

    # Tạo task_id mới
    task_id = str(uuid.uuid4())
    task_status[task_id] = "pending"
    task_results[task_id] = None

    # Khởi chạy task trong background thread
    thread = threading.Thread(target=process_check_phone_task, args=(task_id, phone_number))
    thread.daemon = True
    thread.start()

    # Trả về task_id ngay lập tức
    return jsonify({
        "task_id": task_id,
        "status": "pending",
        "message": "Task started successfully"
    })

@app.route("/check-task-status/<task_id>", methods=["GET"])
def check_task_status(task_id):
    """API endpoint để kiểm tra trạng thái của task"""
    if task_id not in task_status:
        return jsonify({"error": "Task not found"}), 404

    status = task_status[task_id]
    response = {
        "task_id": task_id,
        "status": status
    }

    if status == "completed":
        response["data"] = task_results[task_id]
        # Xóa task đã hoàn thành sau 5 phút
        threading.Timer(300, lambda: cleanup_task(task_id)).start()
    elif status == "error":
        response["error"] = task_results[task_id].get("error", "Unknown error")
        # Xóa task lỗi sau 5 phút
        threading.Timer(300, lambda: cleanup_task(task_id)).start()

    return jsonify(response)

def cleanup_task(task_id):
    """Xóa task và kết quả của nó khỏi bộ nhớ"""
    if task_id in task_status:
        del task_status[task_id]
    if task_id in task_results:
        del task_results[task_id]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


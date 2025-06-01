# test_existing_customer.py

# Import trực tiếp các hàm từ automation_app.py
from auto_dk import _initialize_driver, _login_to_timesoft, _automate_for_existing_customer_sync, MEMBERSHIP_INDEX_MAP_YOGA, MEMBERSHIP_INDEX_MAP_GYM

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def run_test_existing_customer(phone_number, service_type, membership_type):
    """
    Hàm để chạy thử nghiệm tự động hóa khách cũ một cách độc lập.
    """
    print(f"\n--- Bắt đầu Test Tự động hóa Khách cũ ---")
    print(f"Số điện thoại: {phone_number}")
    print(f"Loại dịch vụ: {service_type}")
    print(f"Gói tập: {membership_type}")

    result = _automate_for_existing_customer_sync(phone_number, service_type, membership_type)

    if result["status"] == "success":
        print(f"🎉 Test thành công: {result['message']}")
    else:
        print(f"❌ Test thất bại: {result['message']}")

    print(f"--- Kết thúc Test Tự động hóa Khách cũ ---")

if __name__ == "__main__":
    # --- CẤU HÌNH THÔNG TIN TEST ---
    TEST_PHONE_NUMBER = "0971166684" # Thay bằng SĐT của khách hàng cũ có thật trong hệ thống Timesoft
    TEST_SERVICE_TYPE = "yoga"       # Hoặc "yoga"
    TEST_MEMBERSHIP_TYPE = "1year"  # Các lựa chọn khác: "day", "week", "3months", "6months", "year"

    # Chạy hàm test
    run_test_existing_customer(TEST_PHONE_NUMBER, TEST_SERVICE_TYPE, TEST_MEMBERSHIP_TYPE)

    # --- Ví dụ test với các thông tin khác ---
    # run_test_existing_customer("0987654321", "yoga", "3months")
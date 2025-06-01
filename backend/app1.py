import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
# Cho phép tất cả các nguồn gốc trong môi trường phát triển.
# Trong sản phẩm thực tế, bạn nên giới hạn nó chỉ với domain của frontend.
CORS(app)

# --- CẤU HÌNH HỆ THỐNG THANH TOÁN ---

# Thời gian tối đa để chờ một giao dịch (giây), ví dụ 2 phút
PAYMENT_TIMEOUT_SECONDS = 120

# SỬA LỖI QUAN TRỌNG:
# Sử dụng một dictionary để lưu nhiều giao dịch đang chờ.
# Khóa (key) sẽ là số tiền cần thanh toán (dưới dạng chuỗi),
# và giá trị (value) là thông tin giao dịch.
# LƯU Ý: Trong ứng dụng thực tế, việc dùng số tiền làm khóa có thể rủi ro
# nếu 2 người cùng thanh toán một số tiền. Một mã đơn hàng duy nhất (order_id)
# sẽ là giải pháp tốt hơn. Tuy nhiên, để đơn giản, chúng ta tạm dùng số tiền.
pending_payments = {}


# --- ENDPOINT 1: BẮT ĐẦU PHIÊN THANH TOÁN ---
@app.route('/start-payment-session', methods=['POST'])
def start_payment_session():
    """
    Endpoint này được gọi bởi frontend để bắt đầu một phiên chờ thanh toán.
    Nó nhận thông tin đơn hàng, tính toán số tiền và tạo một giao dịch chờ.
    """
    data = request.get_json()
    if not data or not data.get("service"):
        return jsonify({"status": "error", "message": "Thiếu thông tin dịch vụ."}), 400

    service_info = {
        "service": data.get("service"),
        "membership": data.get("membership"),
        "phoneNumber": data.get("phoneNumber")
    }

    # Giả lập việc tính toán số tiền phải trả.
    # Trong thực tế, bạn nên có logic phức tạp hơn.
    expected_amount = 0
    if service_info["membership"] == "1 day":
        expected_amount = 5000
    elif service_info["membership"] == "1 month":
        expected_amount = 50000
    # Thêm các gói khác ở đây...
    else:
        # Nếu không xác định được gói, trả về lỗi
        return jsonify({"status": "error", "message": "Gói dịch vụ không hợp lệ."}), 400

    # Chuyển số tiền thành chuỗi để dùng làm key
    transaction_key = str(expected_amount)

    # SỬA LỖI: Thêm một giao dịch mới vào dictionary thay vì ghi đè.
    pending_payments[transaction_key] = {
        "status": "pending",  # Trạng thái: pending, success, fail_amount_mismatch, timeout
        "expected_amount": expected_amount,
        "created_at": time.time(),
        "service_info": service_info
    }

    print(f"Đã tạo phiên chờ thanh toán cho số tiền: {expected_amount}")
    print("Các giao dịch đang chờ:", pending_payments)

    return jsonify({
        "status": "session_started",
        "expected_amount": expected_amount,
        "message": "Phiên chờ thanh toán đã bắt đầu. Vui lòng hoàn tất thanh toán."
    })


# --- ENDPOINT 2: KIỂM TRA TRẠNG THÁI THANH TOÁN (POLLING) ---
@app.route('/check-payment-status', methods=['GET'])
def check_payment_status():
    """
    Endpoint này được frontend gọi liên tục (polling) để kiểm tra kết quả.
    Nó nhận `expected_amount` làm tham số truy vấn.
    """
    # Lấy key từ query parameter của URL
    transaction_key = request.args.get('expected_amount')
    if not transaction_key:
        return jsonify({"status": "error", "message": "Thiếu tham số expected_amount."}), 400

    transaction = pending_payments.get(transaction_key)

    if not transaction:
        return jsonify({"status": "not_found", "message": "Không tìm thấy phiên thanh toán."}), 404

    # Kiểm tra nếu phiên đã quá hạn
    elapsed_time = time.time() - transaction["created_at"]
    if transaction["status"] == "pending" and elapsed_time > PAYMENT_TIMEOUT_SECONDS:
        transaction["status"] = "timeout"
        print(f"Phiên cho {transaction_key} đã quá hạn.")

    # Trả về trạng thái hiện tại của giao dịch
    return jsonify({
        "status": transaction["status"],
        "expected_amount": transaction["expected_amount"]
    })


# --- ENDPOINT 3: WEBHOOK NHẬN DỮ LIỆU TỪ SEPAY ---
@app.route('/webhook/sepay', methods=['POST'])
def sepay_webhook():
    """
    Endpoint này chỉ dùng để SePay gọi đến khi có giao dịch mới.
    Nó sẽ tìm và cập nhật trạng thái của một giao dịch đang chờ dựa trên SỐ TIỀN.
    """
    sepay_data = request.get_json()
    print("\n--- Webhook nhận được từ SePay ---")
    print(sepay_data)

    transfer_amount = sepay_data.get("transferAmount")

    # SỬA LỖI: Kiểm tra `transferAmount` có tồn tại hay không
    if transfer_amount is None:
        return jsonify({"success": False, "message": "Dữ liệu webhook thiếu trường 'transferAmount'."}), 400

    # Chuyển số tiền nhận được thành chuỗi để tìm kiếm
    transaction_key = str(transfer_amount)
    transaction_found = False

    # Tìm giao dịch đang chờ khớp với số tiền
    if transaction_key in pending_payments:
        transaction = pending_payments[transaction_key]

        # Chỉ xử lý nếu giao dịch đang ở trạng thái 'pending'
        if transaction["status"] == "pending":
            # Logic cốt lõi: so sánh số tiền. Ở đây chúng đã bằng nhau vì ta dùng nó làm key.
            # Trong một hệ thống thực tế, bạn có thể cần so sánh thêm nội dung chuyển khoản.
            transaction["status"] = "success"
            transaction_found = True
            print(f"✅ Thanh toán THÀNH CÔNG cho số tiền {transfer_amount}. Giao dịch được xác nhận.")

            # (Tùy chọn) Xóa giao dịch đã thành công để dọn dẹp bộ nhớ
            # del pending_payments[transaction_key]
        else:
            print(
                f"Webhook nhận được cho một giao dịch đã được xử lý: {transaction_key} (Trạng thái: {transaction['status']})")

    if not transaction_found:
        print(f"Webhook nhận được cho số tiền {transfer_amount}, nhưng không có giao dịch nào đang chờ khớp.")

    # LUÔN phản hồi cho SePay biết là đã nhận được webhook thành công để họ không gửi lại.
    return jsonify({"success": True}), 200


if __name__ == '__main__':
    # Xóa màn hình console để dễ nhìn khi khởi động lại
    os.system('cls' if os.name == 'nt' else 'clear')
    print("🚀 Máy chủ Flask đang chạy để xác thực thanh toán.")
    print("   - Endpoint để bắt đầu phiên: /start-payment-session (POST)")
    print("   - Endpoint để kiểm tra trạng thái: /check-payment-status (GET)")
    print("   - Endpoint cho SePay webhook: /webhook/sepay (POST)")
    app.run(debug=True, port=5001)
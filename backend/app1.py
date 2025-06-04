import time
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

print("DEBUG: app1.py - SCRIPT LOADING...")

app = Flask(__name__)
CORS(app) # Cho phép CORS cho tất cả các route trên app này
print("DEBUG: app1.py - Flask app created and CORS enabled.")

# Nơi lưu trữ các giao dịch đang chờ thanh toán (trong bộ nhớ)
# Key: order_id (string)
# Value: {'expected_amount': int, 'status': 'pending' | 'success' | 'failed_amount_mismatch' | 'timeout', 'created_at': float_timestamp, 'service_info': {...}}
# CẢNH BÁO: Đây là để demo. Trong production, hãy dùng database (Redis, PostgreSQL, etc.)
pending_payments_by_order_id = {}

PAYMENT_TIMEOUT_SECONDS = 180  # Ví dụ: 3 phút cho một phiên thanh toán

# Endpoint để frontend gọi đến khởi tạo phiên thanh toán
@app.route('/api/app1/initiate-payment', methods=['POST'])
def initiate_payment_session():
    print("[app1.py] Received request for /api/app1/initiate-payment")
    data = request.get_json()
    if not data:
        print("[app1.py] Error: No data received for initiate-payment")
        return jsonify({"success": False, "message": "Không có dữ liệu được cung cấp."}), 400

    # Frontend cần gửi thông tin để backend tính toán số tiền
    # Ví dụ: service_type = data.get("service"), membership_type = data.get("membership")
    service_type = data.get("service")
    membership_type = data.get("membership")
    # phone_number = data.get("phoneNumber") # Có thể lưu lại nếu cần

    if not service_type or not membership_type:
        print(f"[app1.py] Error: Missing service/membership in initiate-payment. Data: {data}")
        return jsonify({"success": False, "message": "Thiếu thông tin dịch vụ hoặc gói thành viên."}), 400

    # --- Logic tính toán số tiền dự kiến (expected_amount) ---
    expected_amount = 0
    # Đây là logic ví dụ, bạn cần thay thế bằng cách tính giá thực tế của mình
    if membership_type == "1 day":
        expected_amount = 5000
    elif membership_type == "1 month":
        expected_amount = 50000
    # Thêm các quy tắc giá khác của bạn ở đây...
    else:
        print(f"[app1.py] Error: Invalid membership_type: {membership_type}")
        return jsonify({"success": False, "message": f"Gói dịch vụ '{membership_type}' không hợp lệ."}), 400

    if expected_amount <= 0:
        print(f"[app1.py] Error: Calculated amount is not positive: {expected_amount}")
        return jsonify({"success": False, "message": "Không thể xác định số tiền thanh toán."}), 400

    # --- Tạo một mã đơn hàng (order_id) duy nhất ---
    # Ví dụ: HD_1678886400_ABCXYZ (Tiền tố HD, timestamp, một vài ký tự hex ngẫu nhiên)
    order_id = f"HD_{int(time.time())}_{os.urandom(3).hex().upper()}"

    pending_payments_by_order_id[order_id] = {
        "expected_amount": expected_amount,
        "status": "pending",
        "created_at": time.time(),
        "service_info": {"service": service_type, "membership": membership_type} # Lưu lại để tham khảo
    }
    print(f"[app1.py] Đã khởi tạo phiên thanh toán: ID {order_id}, Số tiền: {expected_amount}")

    # Nội dung chuyển khoản gợi ý cho mã QR (ngắn gọn, chứa phần cuối order_id)
    # Ví dụ: nếu order_id là "HD_123_ABCDEF", payment_message có thể là "TT ABCDEF"
    # Bạn nên làm cho payment_message này đủ duy nhất để dễ đối soát nếu cần.
    # Hoặc tốt nhất là truyền order_id đầy đủ vào tham số 'referenceCode' của SePay khi tạo QR.
    payment_message = f"TT {order_id}" # Truyền cả order_id vào nội dung cho dễ

    return jsonify({
        "success": True,
        "order_id": order_id,            # Frontend sẽ dùng để kiểm tra trạng thái
        "expected_amount": expected_amount, # Frontend dùng để hiển thị và tạo QR
        "payment_message": payment_message  # Frontend dùng cho nội dung chuyển khoản trên QR
    }), 201 # 201 Created: Resource (phiên thanh toán) đã được tạo


# Endpoint Webhook mà SePay sẽ gọi đến
# Nginx sẽ map /api/app1/webhook/sepay tới route /webhook/sepay này của app1.py
@app.route('/webhook/sepay', methods=['POST'])
def sepay_webhook_listener():
    sepay_data = request.get_json()
    print(f"\n[app1.py] --- Webhook nhận được từ SePay ---")
    print(sepay_data) # In ra toàn bộ dữ liệu webhook để bạn xem cấu trúc của nó

    if not sepay_data:
        print("[app1.py] Webhook: Không nhận được dữ liệu.")
        return jsonify({"success": True, "message": "Webhook nhận được nhưng không có dữ liệu."}), 200

    transfer_amount = sepay_data.get("transferAmount")

    # === QUAN TRỌNG: TRÍCH XUẤT ORDER_ID TỪ WEBHOOK ===
    # Bạn cần xác định SePay gửi order_id của bạn trong trường nào.
    # Ví dụ 1: Nếu bạn đã truyền order_id vào trường 'referenceCode' khi tạo link/QR SePay:
    order_id_from_webhook = sepay_data.get("referenceCode")
    if order_id_from_webhook:
        print(f"[app1.py] Webhook: Tìm thấy 'referenceCode': {order_id_from_webhook}")

    # Ví dụ 2: Nếu order_id nằm trong nội dung/mô tả chuyển khoản (ít tin cậy hơn)
    # Giả sử nội dung chuyển khoản của bạn có dạng "TT HD_..."
    if not order_id_from_webhook:
        description = str(sepay_data.get("description", "") + " " + sepay_data.get("content", "")).strip()
        if description.startswith("TT HD_"): # Nếu bạn dùng format "TT " + order_id
            # Cố gắng tách order_id từ description
            try:
                order_id_from_webhook = description.split("TT ")[1].split(" ")[0]
                print(f"[app1.py] Webhook: Trích xuất order_id từ description: {order_id_from_webhook}")
            except IndexError:
                print(f"[app1.py] Webhook: Không thể trích xuất order_id từ description: '{description}'")
        else:
            print(f"[app1.py] Webhook: Không tìm thấy 'referenceCode' và description không khớp format 'TT HD_...'")


    if transfer_amount is None or not order_id_from_webhook:
        print("[app1.py] Lỗi Webhook: Thiếu transferAmount hoặc không xác định được order_id.")
        return jsonify({"success": True, "message": "Đã nhận webhook nhưng thiếu thông tin quan trọng (số tiền hoặc mã đơn hàng)."}), 200

    transaction = pending_payments_by_order_id.get(str(order_id_from_webhook)) # Đảm bảo key là chuỗi

    if transaction:
        if transaction["status"] == "pending":
            elapsed_time = time.time() - transaction["created_at"]
            if elapsed_time > PAYMENT_TIMEOUT_SECONDS:
                transaction["status"] = "timeout"
                print(f"[app1.py] Webhook: Giao dịch {order_id_from_webhook} đã QUÁ HẠN.")
                return jsonify({"success": True, "message": "Giao dịch đã quá hạn."}), 200

            if int(transfer_amount) == transaction["expected_amount"]:
                transaction["status"] = "success"
                print(f"[app1.py] ✅ Webhook: Thanh toán THÀNH CÔNG cho đơn hàng {order_id_from_webhook}. Số tiền: {transfer_amount}")
                # Tại đây, bạn có thể thực hiện các hành động nghiệp vụ:
                # - Cập nhật trạng thái đơn hàng trong database chính của bạn
                # - Kích hoạt dịch vụ cho người dùng
                # - Gửi email/SMS xác nhận
                #pending_payments_by_order_id.pop(order_id_from_webhook, None) # Xóa nếu không cần lưu nữa
                return jsonify({"success": True, "message": "Xác nhận thanh toán thành công."}), 200 # Hoặc 201
            else:
                transaction["status"] = "failed_amount_mismatch"
                print(f"[app1.py] ⚠️ Webhook: Thanh toán THẤT BẠI cho đơn hàng {order_id_from_webhook}. Sai số tiền. Mong đợi {transaction['expected_amount']}, nhận được {transfer_amount}")
                return jsonify({"success": True, "message": "Đã nhận, nhưng sai số tiền."}), 200
        else:
            print(f"[app1.py] Webhook: Nhận được cho đơn hàng {order_id_from_webhook} đã được xử lý trước đó. Trạng thái hiện tại: {transaction['status']}")
            return jsonify({"success": True, "message": "Giao dịch đã được xử lý trước đó."}), 200
    else:
        print(f"[app1.py] Webhook: Không tìm thấy giao dịch nào đang chờ cho order_id: {order_id_from_webhook}")
        return jsonify({"success": True, "message": "Không tìm thấy giao dịch chờ khớp."}), 200


# Endpoint để frontend kiểm tra trạng thái thanh toán (polling)
@app.route('/api/app1/check-payment-status', methods=['GET'])
def check_payment():
    order_id = request.args.get('order_id')
    print(f"[app1.py] Yêu cầu kiểm tra trạng thái cho order_id: {order_id}")

    if not order_id:
        print("[app1.py] Lỗi: Thiếu order_id cho check-payment-status")
        return jsonify({"success": False, "message": "Thiếu tham số order_id."}), 400

    transaction = pending_payments_by_order_id.get(str(order_id)) # Đảm bảo key là chuỗi

    if not transaction:
        print(f"[app1.py] Không tìm thấy giao dịch cho order_id: {order_id}")
        return jsonify({"success": True, "status": "not_found", "message": "Không tìm thấy phiên thanh toán."}), 200

    # Kiểm tra lại timeout nếu vẫn đang pending (phòng trường hợp webhook bị trễ/mất)
    if transaction["status"] == "pending" and (time.time() - transaction["created_at"] > PAYMENT_TIMEOUT_SECONDS):
        transaction["status"] = "timeout"
        print(f"[app1.py] Kiểm tra trạng thái: Giao dịch {order_id} đã QUÁ HẠN.")

    print(f"[app1.py] Trạng thái cho {order_id}: {transaction['status']}")
    return jsonify({
        "success": True,
        "order_id": order_id,
        "status": transaction["status"], # Sẽ là 'pending', 'success', 'failed_amount_mismatch', hoặc 'timeout'
        "expected_amount": transaction.get("expected_amount")
    }), 200

print("DEBUG: app1.py - Các route đã được định nghĩa.")

if __name__ == '__main__':
    print("DEBUG: app1.py - Chạy trực tiếp với __main__ (dành cho test cục bộ).")
    # Cổng này phải khớp với cổng được cấu hình cho app1 trong supervisord.conf (ví dụ: 5001)
    app.run(host="0.0.0.0", port=5001, debug=True)

print("DEBUG: app1.py - SCRIPT LOADED SUCCESSFULLY.")
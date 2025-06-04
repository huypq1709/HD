# File: backend/app1.py (Cập nhật logic order_id và payment_message)
import time
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

print("DEBUG: app1.py - SCRIPT LOADING...")

app = Flask(__name__)
CORS(app)
print("DEBUG: app1.py - Flask app created and CORS enabled.")

pending_payments_by_order_id = {}
PAYMENT_TIMEOUT_SECONDS = 180

@app.route('/initiate-payment', methods=['POST'])
def initiate_payment_session():
    print("[app1.py] Received request for /initiate-payment")
    data = request.get_json()
    if not data:
        print("[app1.py] Error: No data received for initiate-payment")
        return jsonify({"success": False, "message": "Không có dữ liệu được cung cấp."}), 400

    service_type = data.get("service")
    membership_type = data.get("membership")

    if not service_type or not membership_type:
        print(f"[app1.py] Error: Missing service/membership in initiate-payment. Data: {data}")
        return jsonify({"success": False, "message": "Thiếu thông tin dịch vụ hoặc gói thành viên."}), 400

    expected_amount = 0
    if membership_type == "1 day":
        expected_amount = 10000 # Giả sử bạn đã sửa giá ở đây
    elif membership_type == "1 month":
        expected_amount = 50000
    else:
        print(f"[app1.py] Error: Invalid membership_type: {membership_type}")
        return jsonify({"success": False, "message": f"Gói dịch vụ '{membership_type}' không hợp lệ."}), 400

    if expected_amount <= 0:
        print(f"[app1.py] Error: Calculated amount is not positive: {expected_amount}")
        return jsonify({"success": False, "message": "Không thể xác định số tiền thanh toán."}), 400

    timestamp_part = str(int(time.time()))
    random_part = os.urandom(3).hex().upper()
    # order_id giờ bao gồm "TT "
    order_id = f"TT HD{timestamp_part}{random_part}"

    pending_payments_by_order_id[order_id] = {
        "expected_amount": expected_amount,
        "status": "pending",
        "created_at": time.time(),
        "service_info": {"service": service_type, "membership": membership_type}
    }
    print(f"[app1.py] Initiated payment session: ID {order_id}, Amount: {expected_amount}")

    payment_message = order_id # payment_message chính là order_id

    return jsonify({
        "success": True,
        "order_id": order_id,
        "expected_amount": expected_amount,
        "payment_message": payment_message
    }), 201

@app.route('/webhook/sepay', methods=['POST'])
def sepay_webhook_listener():
    sepay_data = request.get_json()
    print(f"\n[app1.py] --- SePay Webhook Received ---")
    print(sepay_data)

    if not sepay_data:
        print("[app1.py] Webhook: Empty data received.")
        return jsonify({"success": True, "message": "Empty data."}), 200

    transfer_amount = sepay_data.get("transferAmount")

    order_id_from_webhook = None
    content_from_webhook = str(sepay_data.get("content", "")).strip()

    print(f"[app1.py] Webhook: Received content from SePay: '{content_from_webhook}'")

    if content_from_webhook.startswith("TT HD"):
        order_id_from_webhook = content_from_webhook
        print(f"[app1.py] Webhook: Using 'content' directly as order_id: {order_id_from_webhook}")
    else:
        print(f"[app1.py] Webhook: 'content' ('{content_from_webhook}') không khớp format 'TT HD...' mong đợi. Thử kiểm tra 'referenceCode'.")
        raw_reference_code = sepay_data.get("referenceCode")
        if raw_reference_code and str(raw_reference_code).strip().startswith("TT HD"):
            order_id_from_webhook = str(raw_reference_code).strip()
            print(f"[app1.py] Webhook: Lấy order_id từ 'referenceCode' làm fallback: {order_id_from_webhook}")

    if transfer_amount is None or not order_id_from_webhook:
        print(f"[app1.py] Lỗi Webhook: Thiếu transferAmount ({transfer_amount}) hoặc không xác định được order_id ({order_id_from_webhook}).")
        return jsonify({"success": True, "message": "Đã nhận webhook nhưng thiếu thông tin quan trọng hoặc format không đúng."}), 200

    transaction = pending_payments_by_order_id.get(order_id_from_webhook)

    if transaction:
        if transaction["status"] == "pending":
            elapsed_time = time.time() - transaction["created_at"]
            if elapsed_time > PAYMENT_TIMEOUT_SECONDS:
                pending_payments_by_order_id[order_id_from_webhook]["status"] = "timeout"
                print(f"[app1.py] Webhook: Giao dịch {order_id_from_webhook} đã QUÁ HẠN.")
                return jsonify({"success": True, "message": "Giao dịch đã quá hạn."}), 200

            if int(transfer_amount) == transaction["expected_amount"]:
                pending_payments_by_order_id[order_id_from_webhook]["status"] = "success"
                print(f"[app1.py] ✅ Webhook: Thanh toán THÀNH CÔNG cho đơn hàng {order_id_from_webhook}. Số tiền: {transfer_amount}")
                return jsonify({"success": True, "message": "Xác nhận thanh toán thành công."}), 200
            else:
                pending_payments_by_order_id[order_id_from_webhook]["status"] = "failed_amount_mismatch"
                print(f"[app1.py] ⚠️ Webhook: Thanh toán THẤT BẠI cho đơn hàng {order_id_from_webhook}: Sai số tiền. Mong đợi {transaction['expected_amount']}, nhận được {transfer_amount}")
                return jsonify({"success": True, "message": "Đã nhận, sai số tiền."}), 200
        else:
            print(f"[app1.py] Webhook: Nhận được cho đơn hàng {order_id_from_webhook} đã được xử lý trước đó. Trạng thái: {transaction['status']}")
            return jsonify({"success": True, "message": "Giao dịch đã được xử lý trước đó."}), 200
    else:
        print(f"[app1.py] Webhook: Không tìm thấy giao dịch nào đang chờ cho order_id: {order_id_from_webhook}")
        return jsonify({"success": True, "message": "Không tìm thấy giao dịch chờ khớp."}), 200

@app.route('/check-payment-status', methods=['GET'])
def check_payment():
    order_id = request.args.get('order_id')
    print(f"[app1.py] Yêu cầu kiểm tra trạng thái cho order_id: {order_id}")

    if not order_id:
        print("[app1.py] Lỗi: Thiếu order_id cho check-payment-status")
        return jsonify({"success": False, "message": "Thiếu tham số order_id."}), 400

    transaction = pending_payments_by_order_id.get(str(order_id))

    if not transaction:
        print(f"[app1.py] Không tìm thấy giao dịch cho order_id: {order_id}")
        return jsonify({"success": True, "status": "not_found", "message": "Không tìm thấy phiên thanh toán."}), 200

    if transaction["status"] == "pending" and (time.time() - transaction["created_at"] > PAYMENT_TIMEOUT_SECONDS):
        pending_payments_by_order_id[str(order_id)]["status"] = "timeout" # Cập nhật trạng thái
        print(f"[app1.py] Kiểm tra trạng thái: Giao dịch {order_id} đã QUÁ HẠN.")

    print(f"[app1.py] Trạng thái cho {order_id}: {transaction['status']}")
    return jsonify({
        "success": True,
        "order_id": order_id,
        "status": transaction["status"],
        "expected_amount": transaction.get("expected_amount")
    }), 200

print("DEBUG: app1.py - Các route đã được định nghĩa.")

if __name__ == '__main__':
    print("DEBUG: app1.py - Chạy trực tiếp với __main__ (dành cho test cục bộ).")
    app.run(host="0.0.0.0", port=5001, debug=True)

print("DEBUG: app1.py - SCRIPT LOADED SUCCESSFULLY.")
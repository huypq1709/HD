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

def calculate_membership_price(membership_type, customer_type=None, service_type=None):
    if membership_type == "1 day":
        if service_type == "gym":
            return 60000
        return 0  # No 1-day pass for yoga

    # Base monthly price is same for both gym and yoga
    BASE_MONTHLY_PRICE_VND = 600000
    
    DURATION_IN_MONTHS = {
        "1 month": 1,
        "3 months": 3,
        "6 months": 6,
        "1 year": 12,
    }
    STANDARD_DURATION_DISCOUNTS = {
        "1 month": 0,
        "3 months": 0.10,
        "6 months": 0.15,
        "1 year": 0.20,
    }
    PROMO_DISCOUNTS_OLD_CUSTOMER = {
        "1 month": 0.05,
        "3 months": 0.10,
        "6 months": 0.15,
        "1 year": 0.15,
    }
    PROMO_DISCOUNTS_NEW_CUSTOMER = {
        "1 month": 0.10,
        "3 months": 0.15,
        "6 months": 0.25,
        "1 year": 0.30,
    }
    months = DURATION_IN_MONTHS.get(membership_type)
    if not months:
        return 0
    total_gross = BASE_MONTHLY_PRICE_VND * months
    standard_discount = STANDARD_DURATION_DISCOUNTS.get(membership_type, 0)
    price_after_standard = total_gross * (1 - standard_discount)
    promo_discount = 0
    if customer_type == "returning":
        promo_discount = PROMO_DISCOUNTS_OLD_CUSTOMER.get(membership_type, 0)
    elif customer_type == "new":
        promo_discount = PROMO_DISCOUNTS_NEW_CUSTOMER.get(membership_type, 0)
    final_price = price_after_standard * (1 - promo_discount)
    return round(final_price)

@app.route('/initiate-payment', methods=['POST'])
def initiate_payment_session():
    print("[app1.py] Received request for /initiate-payment")
    data = request.get_json()
    if not data:
        print("[app1.py] Error: No data received for initiate-payment")
        return jsonify({"success": False, "message": "Không có dữ liệu được cung cấp."}), 400

    service_type = data.get("service")
    membership_type = data.get("membership")
    customer_type = data.get("customerType")

    print(f"[app1.py] Nhận membership_type: {membership_type!r}, customer_type: {customer_type!r}")
    expected_amount = calculate_membership_price(membership_type, customer_type, service_type)
    print(f"[app1.py] Tính ra expected_amount: {expected_amount}")

    if not service_type or not membership_type:
        print(f"[app1.py] Error: Missing service/membership in initiate-payment. Data: {data}")
        return jsonify({"success": False, "message": "Thiếu thông tin dịch vụ hoặc gói thành viên."}), 400

    if expected_amount <= 0:
        print(f"[app1.py] Error: Calculated amount is not positive: {expected_amount}")
        return jsonify({"success": False, "message": "Không thể xác định số tiền thanh toán."}), 400

    timestamp_part = str(int(time.time()))
    random_part = os.urandom(3).hex().upper()
    order_id = f"TT HD{timestamp_part}{random_part}"

    pending_payments_by_order_id[order_id] = {
        "expected_amount": expected_amount,
        "status": "pending",
        "created_at": time.time(),
        "service_info": {"service": service_type, "membership": membership_type, "customerType": customer_type}
    }
    print(f"[app1.py] Initiated payment session: ID {order_id}, Amount: {expected_amount}")

    payment_message = order_id

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
    content_from_webhook = str(sepay_data.get("content", "")).strip()
    
    print(f"[app1.py] Webhook: Received content from SePay: '{content_from_webhook}'")

    # Tìm order_id trong content (format: ...-TT HD...)
    order_id_from_webhook = None
    if "TT HD" in content_from_webhook:
        # Tìm phần sau "TT HD" trong content
        tt_hd_index = content_from_webhook.find("TT HD")
        if tt_hd_index != -1:
            order_id_from_webhook = content_from_webhook[tt_hd_index:]
            print(f"[app1.py] Webhook: Extracted order_id from content: {order_id_from_webhook}")

    if not order_id_from_webhook:
        print(f"[app1.py] Webhook: Could not find 'TT HD' in content. Trying referenceCode...")
        raw_reference_code = sepay_data.get("referenceCode")
        if raw_reference_code and str(raw_reference_code).strip().startswith("TT HD"):
            order_id_from_webhook = str(raw_reference_code).strip()
            print(f"[app1.py] Webhook: Using referenceCode as order_id: {order_id_from_webhook}")

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
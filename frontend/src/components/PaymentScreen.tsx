import React, { useEffect, useState, useRef, useCallback } from "react";
import { Slogan } from "./Slogan"; // Giả sử bạn có component này
// import Loader from "./Loader"; // Nếu bạn muốn hiển thị loader

interface PaymentScreenProps {
    formData: {
        service: string;
        membership: string;
        phoneNumber: string;
        // membershipPriceFormatted không còn cần thiết nếu backend tính và trả về giá
        [key: string]: any;
    };
    nextStep: () => void;
    prevStep: () => void;
    language: string;
    resetToIntro: () => void; // Hàm để quay về step 0 và reset form ở App.tsx
    resetFormData: () => void; // Hàm để reset form data ở App.tsx
}

// Thông tin ngân hàng của bạn (có thể đặt ở file config)
const MY_BANK_ACCOUNT = "07019218501";
const MY_BANK_NAME_VIETQR_ID = "TPB"; // Mã VietQR ID cho TPBank
const MY_ACCOUNT_HOLDER = "PHAM QUANG HUY";

export function PaymentScreen({
                                  formData,
                                  nextStep,
                                  prevStep,
                                  language,
                                  resetToIntro,
                                  resetFormData,
                              }: PaymentScreenProps) {
    const [timeLeft, setTimeLeft] = useState(120); // 2 phút = 120 giây
    const [paymentStatus, setPaymentStatus] = useState<string>("initializing"); // initializing, pending, success, timeout, error_session, error_polling, failed_amount_mismatch
    const [statusMessage, setStatusMessage] = useState<string>(
        language === "en" ? "Initializing payment session..." : "Đang khởi tạo phiên thanh toán..."
    );
    const [qrCodeUrl, setQrCodeUrl] = useState<string>("");
    const [paymentDetails, setPaymentDetails] = useState<{
        orderId: string | null;
        expectedAmount: number | null;
        paymentMessage: string | null;
    }>({
        orderId: null,
        expectedAmount: null,
        paymentMessage: null,
    });

    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const hasNavigatedRef = useRef(false); // Chống việc điều hướng/reset nhiều lần

    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;

    const stopPolling = useCallback(() => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
    }, []);

    const stopTimer = useCallback(() => {
        if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
        }
    }, []);

    // EFFECT 1: Khởi tạo phiên thanh toán và tạo mã QR khi component được mount
    useEffect(() => {
        const initiateAndGenerateQR = async () => {
            if (paymentDetails.orderId) return; // Chỉ chạy một lần

            try {
                const response = await fetch("/api/app1/initiate-payment", { // Đảm bảo app1 là nơi xử lý
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        service: formData.service,
                        membership: formData.membership,
                        phoneNumber: formData.phoneNumber,
                    }),
                });

                const data = await response.json();

                if (response.ok && data.success && data.order_id && data.expected_amount && data.payment_message) {
                    console.log("Payment session initiated:", data);
                    setPaymentDetails({
                        orderId: data.order_id,
                        expectedAmount: data.expected_amount,
                        paymentMessage: data.payment_message,
                    });

                    const qrUrl = `https://qr.sepay.vn/img?acc=${MY_BANK_ACCOUNT}&bank=${MY_BANK_NAME_VIETQR_ID}&amount=${data.expected_amount}&des=${encodeURIComponent(data.payment_message)}&template=compact2`;
                    setQrCodeUrl(qrUrl);

                    setPaymentStatus("pending");
                    // Status message sẽ được cập nhật bởi useEffect theo dõi paymentStatus
                } else {
                    throw new Error(data.message || (language === "en" ? "Failed to start payment session." : "Khởi tạo phiên thanh toán thất bại."));
                }
            } catch (error: any) {
                console.error("Error initiating payment session:", error);
                setPaymentStatus("error_session");
                setStatusMessage(error.message || (language === "en" ? "Error initializing. Please try again." : "Lỗi khởi tạo. Vui lòng thử lại."));
            }
        };

        initiateAndGenerateQR();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Chạy một lần duy nhất

    // EFFECT 2: Polling kiểm tra trạng thái thanh toán
    useEffect(() => {
        if (paymentDetails.orderId && paymentStatus === "pending" && !hasNavigatedRef.current) {
            if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current); // Xóa interval cũ nếu có

            pollingIntervalRef.current = setInterval(async () => {
                try {
                    const response = await fetch(`/api/app1/check-payment-status?order_id=${paymentDetails.orderId}`);
                    const result = await response.json();
                    console.log("Polling result:", result);

                    if (result.success && result.status && result.status !== "pending" && result.status !== "not_found") {
                        setPaymentStatus(result.status); // success, failed_amount_mismatch, timeout (từ backend)
                        stopPolling(); // Dừng polling khi có kết quả cuối cùng
                        stopTimer();   // Dừng cả timer đếm ngược
                    } else if (result.status === "not_found") {
                        // Nếu backend báo not_found (ví dụ do orderId sai hoặc đã bị xóa vì quá hạn từ lâu)
                        setPaymentStatus("error_polling");
                        setStatusMessage(language === "en" ? "Payment session not found. Please restart." : "Không tìm thấy phiên thanh toán. Vui lòng bắt đầu lại.");
                        stopPolling();
                        stopTimer();
                    }
                } catch (error) {
                    console.error("Polling error:", error);
                    // Không setPaymentStatus("error") ngay để tránh dừng polling quá sớm do lỗi mạng tạm thời
                    // Có thể thêm logic đếm số lần lỗi polling liên tiếp
                }
            }, 3000); // Polling mỗi 3 giây
        }

        return () => {
            stopPolling();
        };
    }, [paymentDetails.orderId, paymentStatus, language, stopPolling, stopTimer]);

    // EFFECT 3: Bộ đếm ngược và xử lý timeout từ phía UI
    useEffect(() => {
        if (paymentStatus === 'pending' && !hasNavigatedRef.current) {
            if (timeLeft === 0) {
                stopTimer();
                setPaymentStatus("timeout_ui"); // Đặt một trạng thái timeout riêng của UI
                return;
            }
            timerIntervalRef.current = setInterval(() => {
                setTimeLeft((prevTime) => (prevTime > 0 ? prevTime - 1 : 0));
            }, 1000);
        } else {
            stopTimer(); // Dừng timer nếu không còn pending hoặc đã navigate
        }
        return () => {
            stopTimer();
        };
    }, [timeLeft, paymentStatus, stopTimer]);

    // EFFECT 4: Xử lý thay đổi trạng thái thanh toán (để cập nhật UI và điều hướng)
    useEffect(() => {
        if (hasNavigatedRef.current) return;

        switch (paymentStatus) {
            case "initializing":
                setStatusMessage(language === "en" ? "Initializing payment session..." : "Đang khởi tạo phiên thanh toán...");
                break;
            case "pending":
                setStatusMessage(language === "en" ? "Scan QR to pay. Waiting for payment..." : "Quét mã QR. Đang chờ thanh toán...");
                break;
            case "success":
                stopPolling(); stopTimer();
                hasNavigatedRef.current = true;
                setStatusMessage(language === "en" ? "Payment successful! Redirecting..." : "Thanh toán thành công! Đang chuyển hướng...");
                setTimeout(() => {
                    nextStep(); // Chuyển đến màn hình xác nhận
                }, 2000);
                break;
            case "failed_amount_mismatch":
                stopPolling(); stopTimer();
                setStatusMessage(language === "en" ? "Payment failed: Amount mismatch. Contact support." : "Thanh toán thất bại: Sai số tiền. Vui lòng liên hệ hỗ trợ.");
                break;
            case "timeout": // Timeout từ backend (webhook hoặc check-status)
            case "timeout_ui": // Timeout từ bộ đếm ngược của UI
                stopPolling(); stopTimer();
                if (!hasNavigatedRef.current) {
                    hasNavigatedRef.current = true;
                    setStatusMessage(language === "en" ? "Payment timed out. Returning to home..." : "Hết thời gian thanh toán. Đang quay về trang chủ...");
                    resetFormData();
                    // localStorage.removeItem("phoneNumber"); // Nếu bạn có lưu
                    setTimeout(() => {
                        resetToIntro();
                    }, 3000);
                }
                break;
            case "error_session":
            case "error_polling":
                // statusMessage đã được set khi lỗi xảy ra
                stopPolling(); stopTimer();
                // Có thể thêm nút thử lại hoặc tự động quay về sau một lúc
                break;
            default:
                break;
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [paymentStatus, language, nextStep, resetToIntro, resetFormData]); // Không thêm statusMessage vào đây để tránh vòng lặp


    const getMembershipNameDisplay = (membershipId: string, lang: string) => {
        const names: { [key: string]: { en: string; vi: string } } = {
            "1 day": { en: "1 Day Pass", vi: "Gói 1 Ngày" },
            "1 month": { en: "1 Month Pass", vi: "Gói 1 Tháng" },
            // Thêm các gói khác của bạn ở đây
        };
        return names[membershipId]?.[lang as "en" | "vi"] || membershipId;
    };

    const cleanServiceName = (rawService: string) => rawService.replace(/\s*\(.*?\)/g, "").trim();

    const formatCurrency = (amount: number | null) => {
        if (amount === null || amount === undefined) return language === "en" ? "Calculating..." : "Đang tính...";
        return amount.toLocaleString('vi-VN', { style: 'currency', currency: 'VND' });
    };

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
                {language === "en" ? "Payment Information" : "Thông Tin Thanh Toán"}
            </h2>

            <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-gray-800">{language === "en" ? "Order Summary" : "Tóm Tắt Đơn Hàng"}</h3>
                <div className="mt-2 flex justify-between">
                    <span className="text-gray-600">
                        {cleanServiceName(formData.service)} - {getMembershipNameDisplay(formData.membership, language)}
                    </span>
                    <span className="font-semibold">{formatCurrency(paymentDetails.expectedAmount)}</span>
                </div>
            </div>

            <div className="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4">
                <div className="w-full md:w-1/2 text-center p-6 border-2 border-dashed border-gray-300 rounded-lg flex flex-col justify-between min-h-[200px]">
                    <div>
                        <h3 className="text-2xl font-semibold text-gray-800">
                            {paymentStatus === 'pending' ?
                                (language === "en" ? "Payment in" : "Thanh toán trong") :
                                (language === "en" ? "Payment Status" : "Trạng thái TT")}
                        </h3>
                        {paymentStatus === 'pending' && (
                            <p className="mt-2 text-6xl font-bold text-red-500">
                                {minutes}:{seconds < 10 ? `0${seconds}` : seconds}
                            </p>
                        )}
                    </div>
                    <p className="mt-4 text-lg font-medium text-blue-600 h-10">{statusMessage}</p>
                </div>

                <div className="w-full md:w-1/2 text-center p-6 border-2 border-dashed border-gray-300 rounded-lg">
                    {qrCodeUrl ? (
                        <img src={qrCodeUrl} alt="QR Code SePay" className="h-48 w-48 mx-auto object-contain" />
                    ) : (
                        <p>{language === "en" ? "Generating QR Code..." : "Đang tạo mã QR..."}</p>
                    )}
                    <p className="mt-4 text-sm text-gray-600 leading-tight">
                        {language === "en" ? "Scan QR to pay" : "Quét mã QR để thanh toán"}
                        <br />
                        {language === "en" ? "Account Holder: " : "Chủ tài khoản: "}<b>{MY_ACCOUNT_HOLDER}</b>
                        <br />
                        {language === "en" ? "Bank: " : "Ngân hàng: "}<b>TPBank</b>
                        <br />
                        {language === "en" ? "Account No.: " : "Số tài khoản: "}<b>{MY_BANK_ACCOUNT}</b>
                        <br />
                        {paymentDetails.paymentMessage && (
                            <>
                                {language === "en" ? "Content: " : "Nội dung: "}<b>{paymentDetails.paymentMessage}</b>
                            </>
                        )}
                    </p>
                </div>
            </div>

            <div className="flex justify-start pt-4">
                <button
                    onClick={prevStep}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 disabled:opacity-50"
                    disabled={paymentStatus !== 'initializing' && paymentStatus !== 'pending'}
                >
                    {language === "en" ? "Back" : "Quay lại"}
                </button>
            </div>

            <Slogan message={language === "en" ? "Maintain cleanliness and hygiene." : "Duy trì vệ sinh và sạch sẽ."} language={language} />
        </div>
    );
}

// export default PaymentScreen; // Bỏ comment dòng này nếu đây là file riêng
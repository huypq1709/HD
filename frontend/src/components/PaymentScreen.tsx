import React, { useEffect, useState, useRef, useCallback } from "react";
import { Slogan } from "./Slogan";
// import Loader from "./Loader"; // Nếu bạn có loader

interface PaymentScreenProps {
    formData: {
        customerType: string;
        fullName: string;
        phoneNumber: string;
        service: string;
        membership: string;
    };
    updateFormData: (field: string, value: any) => void;
    nextStep: () => void; // Hàm để chuyển sang ConfirmationScreen (step 7)
    prevStep: () => void;
    language: string;
    resetToIntro: () => void;
    resetFormData: () => void;
}

const MY_BANK_ACCOUNT = "0288639397979";
const MY_BANK_NAME_VIETQR_ID = "MB"; // MBBank
const MY_ACCOUNT_HOLDER = "CAO THI HOA"
const PAYMENT_UI_TIMEOUT_SECONDS = 120; // 2 phút

// Thêm object giá gói tập cho Yoga
const YOGA_BASE_PRICES: { [key: string]: number } = {
    "1 month": 600000,
    "3 months": 1620000,
    "6 months": 3060000,
    "1 year": 5760000,
};

// Hàm tính giá gói tập giống MembershipScreen
// const calculateMembershipPrice = (membershipId: string, customerType: string): number => {
//     if (membershipId === "1 day") return 60000;
//     const BASE_MONTHLY_PRICE_VND = 600000;
//     const DURATION_IN_MONTHS: { [key: string]: number } = {
//         "1 month": 1,
//         "3 months": 3,
//         "6 months": 6,
//         "1 year": 12,
//     };
//     const STANDARD_DURATION_DISCOUNTS: { [key: string]: number } = {
//         "1 month": 0,
//         "3 months": 0.10,
//         "6 months": 0.15,
//         "1 year": 0.20,
//     };
//     const PROMO_DISCOUNTS_OLD_CUSTOMER: { [key: string]: number } = {
//         "1 month": 0.05,
//         "3 months": 0.10,
//         "6 months": 0.15,
//         "1 year": 0.15,
//     };
//     const PROMO_DISCOUNTS_NEW_CUSTOMER: { [key: string]: number } = {
//         "1 month": 0.10,
//         "3 months": 0.15,
//         "6 months": 0.25,
//         "1 year": 0.30,
//     };
//     const months = DURATION_IN_MONTHS[membershipId];
//     if (!months) return 0;
//     const totalGrossPrice = BASE_MONTHLY_PRICE_VND * months;
//     const standardDiscountRate = STANDARD_DURATION_DISCOUNTS[membershipId] ?? 0;
//     const priceAfterStandardDiscount = totalGrossPrice * (1 - standardDiscountRate);
//     let promotionalDiscountRate = 0;
//     if (customerType === "returning" && PROMO_DISCOUNTS_OLD_CUSTOMER[membershipId] !== undefined) {
//         promotionalDiscountRate = PROMO_DISCOUNTS_OLD_CUSTOMER[membershipId];
//     } else if (customerType === "new" && PROMO_DISCOUNTS_NEW_CUSTOMER[membershipId] !== undefined) {
//         promotionalDiscountRate = PROMO_DISCOUNTS_NEW_CUSTOMER[membershipId];
//     }
//     const finalPrice = priceAfterStandardDiscount * (1 - promotionalDiscountRate);
//     return Math.round(finalPrice);
// };

export function PaymentScreen({
                                  formData,
                                  updateFormData,
                                  nextStep,
                                  prevStep,
                                  language,
                                  resetToIntro,
                                  resetFormData,
                              }: PaymentScreenProps) {
    const [timeLeft, setTimeLeft] = useState(PAYMENT_UI_TIMEOUT_SECONDS);
    const [paymentStatus, setPaymentStatus] = useState<string>("initializing");
    const [statusMessage, setStatusMessage] = useState<string>(""); // Sẽ được đặt bởi useEffect
    const [qrCodeUrl, setQrCodeUrl] = useState<string>("");
    const [paymentDetails, setPaymentDetails] = useState<{
        orderId: string | null;
        expectedAmount: number | null;
        paymentMessage: string | null;
    }>({ orderId: null, expectedAmount: null, paymentMessage: null });

    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const hasNavigatedOrTimedOutRef = useRef(false); // Chống gọi điều hướng/timeout nhiều lần

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

    // EFFECT 1: Khởi tạo phiên và tạo QR
    useEffect(() => {
        if (!paymentDetails.orderId && !hasNavigatedOrTimedOutRef.current) {
            setPaymentStatus("initializing");
            const initiateAndGenerateQR = async () => {
                try {
                    const response = await fetch("/api/app1/initiate-payment", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            service: formData.service,
                            membership: formData.membership,
                            phoneNumber: formData.phoneNumber,
                            customerType: formData.customerType,
                        }),
                    });
                    const data = await response.json();
                    if (response.ok && data.success && data.order_id && data.payment_message && data.expected_amount) {
                        setPaymentDetails({
                            orderId: data.order_id,
                            expectedAmount: data.expected_amount,
                            paymentMessage: data.payment_message,
                        });
                        // Tạo QR với đúng số tiền trả về từ backend
                        const qrUrl = `https://qr.sepay.vn/img?acc=${MY_BANK_ACCOUNT}&bank=${MY_BANK_NAME_VIETQR_ID}&amount=${data.expected_amount}&des=${encodeURIComponent(data.payment_message)}&template=compact2`;
                        setQrCodeUrl(qrUrl);
                        setPaymentStatus("pending");
                    } else {
                        throw new Error(data.message || "Failed to start payment session.");
                    }
                } catch (error: any) {
                    console.error("Error initiating payment session:", error);
                    setPaymentStatus("error_session");
                }
            };
            initiateAndGenerateQR();
        }
    }, [formData.membership, formData.service, formData.phoneNumber, formData.customerType]);

    // EFFECT 2: Polling kiểm tra trạng thái
    useEffect(() => {
        if (paymentDetails.orderId && paymentStatus === "pending" && !hasNavigatedOrTimedOutRef.current) {
            if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = setInterval(async () => {
                try {
                    const response = await fetch(`/api/app1/check-payment-status?order_id=${paymentDetails.orderId}`);
                    const result = await response.json();
                    console.log("Polling result for order", paymentDetails.orderId, ":", result);
                    if (result.success && result.status && result.status !== "pending" && result.status !== "not_found") {
                        setPaymentStatus(result.status); // Cập nhật trạng thái cuối cùng
                        // Không dừng polling ở đây, để useEffect xử lý trạng thái dừng
                    } else if (result.status === "not_found") {
                        setPaymentStatus("error_polling"); // Phiên không tìm thấy
                    }
                } catch (error) {
                    console.error("Polling error:", error);
                    // Có thể thêm logic retry hoặc thông báo lỗi nếu polling thất bại nhiều lần
                }
            }, 3000);
        }
        return () => stopPolling();
    }, [paymentDetails.orderId, paymentStatus, stopPolling]);

    // EFFECT 3: Bộ đếm ngược thời gian
    useEffect(() => {
        if (paymentStatus === 'pending' && !hasNavigatedOrTimedOutRef.current) {
            if (timeLeft === 0) {
                stopTimer();
                setPaymentStatus("timeout_ui"); // Đặt trạng thái timeout từ UI
                return;
            }
            timerIntervalRef.current = setInterval(() => {
                setTimeLeft((prevTime) => (prevTime > 0 ? prevTime - 1 : 0));
            }, 1000);
        } else {
            stopTimer(); // Dừng timer nếu không còn pending hoặc đã xử lý timeout/success
        }
        return () => stopTimer();
    }, [timeLeft, paymentStatus, stopTimer]);

    // EFFECT 4: Xử lý logic dựa trên thay đổi paymentStatus
    useEffect(() => {
        if (hasNavigatedOrTimedOutRef.current) return; // Nếu đã xử lý, không làm gì nữa

        let newMessage = "";
        let shouldStopActivities = false;

        switch (paymentStatus) {
            case "initializing":
                newMessage = language === "en" ? "Initializing payment session..." : "Đang khởi tạo phiên thanh toán...";
                break;
            case "pending":
                newMessage = language === "en" ? "Scan QR to pay. Waiting for payment..." : "Quét mã QR. Đang chờ thanh toán...";
                break;
            case "success":
                newMessage = language === "en" ? "Payment successful! Redirecting..." : "Thanh toán thành công! Đang chuyển hướng...";
                shouldStopActivities = true;
                hasNavigatedOrTimedOutRef.current = true; // Đánh dấu đã xử lý
                setTimeout(() => {
                    nextStep(); // Chuyển sang ConfirmationScreen
                }, 2000);
                break;
            case "failed_amount_mismatch":
                newMessage = language === "en" ? "Payment failed: Amount mismatch. Contact support." : "Thanh toán thất bại: Sai số tiền. Vui lòng liên hệ hỗ trợ.";
                shouldStopActivities = true;
                break;
            case "timeout_ui": // Timeout do UI đếm ngược
            case "timeout":    // Timeout do backend thông báo (ví dụ qua polling)
                newMessage = language === "en" ? "Payment timed out. Returning to home..." : "Hết thời gian thanh toán. Đang quay về trang chủ...";
                shouldStopActivities = true;
                if (!hasNavigatedOrTimedOutRef.current) { // Đảm bảo reset và điều hướng chỉ 1 lần
                    hasNavigatedOrTimedOutRef.current = true;
                    resetFormData();
                    setTimeout(() => {
                        resetToIntro();
                    }, 3000);
                }
                break;
            case "error_session":
                newMessage = language === "en" ? "Error initializing. Please try again or go back." : "Lỗi khởi tạo phiên. Vui lòng thử lại hoặc quay lại.";
                shouldStopActivities = true;
                break;
            case "error_polling":
                newMessage = language === "en" ? "Could not check payment status. Please check your connection or go back." : "Không thể kiểm tra trạng thái thanh toán. Vui lòng kiểm tra kết nối hoặc quay lại.";
                shouldStopActivities = true;
                if (!hasNavigatedOrTimedOutRef.current) {
                    hasNavigatedOrTimedOutRef.current = true;
                    setTimeout(() => {
                        resetToIntro();
                    }, 10000); // Quay về home sau 10 giây
                }
                break;
            default:
                // Giữ nguyên statusMessage nếu không khớp case nào
                return;
        }

        setStatusMessage(newMessage);

        if (shouldStopActivities) {
            stopPolling();
            stopTimer();
        }
    }, [paymentStatus, language, nextStep, resetToIntro, resetFormData, stopPolling, stopTimer]);
    // Helper để lấy giá hiển thị (dùng cho hiển thị tóm tắt đơn hàng nếu cần)
    const getDisplayPrice = () => {
        if (formData.service === "yoga") {
            const basePrice = YOGA_BASE_PRICES[formData.membership];
            if (!basePrice) return "...";
            return basePrice.toLocaleString("vi-VN") + " VND";
        }
        // Gym: lấy từ paymentDetails.expectedAmount trả về từ backend
        if (paymentDetails.expectedAmount)
            return paymentDetails.expectedAmount.toLocaleString("vi-VN") + " VND";
        return "...";
    };

    // Các hàm helper và JSX render giữ nguyên như bạn đã có
    const getMembershipNameDisplay = (membershipId: string, lang: string) => { /* ... */ return membershipId; };
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
                    <span className="font-semibold text-blue-600">
                        {getDisplayPrice()}
                    </span>
                </div>
            </div>
            {/* === THÊM KHỐI THÔNG BÁO NÀY VÀO === */}
            <div className="mt-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700">
                <p className="font-bold">
                    {language === 'en' ? 'Important Note' : 'Lưu ý Quan trọng'}
                </p>
                {formData.customerType === 'new' && (
                    <p>
                        {language === 'en'
                            ? 'As a new member, after successful payment, you will be redirected to the Face ID update screen.'
                            : 'Vì là khách hàng mới, sau khi thanh toán thành công, quý khách sẽ được chuyển tiếp sang màn hình cập nhật khuôn mặt.'}
                    </p>
                )}
                {formData.customerType === 'returning' && (
                    <p>
                        {language === 'en'
                            ? 'As a returning member, you do not need to update your Face ID again. The process will complete after payment.'
                            : 'Vì là khách hàng cũ, quý khách không cần phải cập nhật lại khuôn mặt. Quá trình sẽ hoàn tất sau khi thanh toán.'}
                    </p>
                )}
            </div>
            {/* === KẾT THÚC KHỐI THÔNG BÁO === */}

            <div className="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4">
                <div className="w-full md:w-1/2 text-center p-6 border-2 border-dashed border-gray-300 rounded-lg flex flex-col justify-between min-h-[200px]">
                    <div>
                        <h3 className="text-2xl font-semibold text-gray-800">
                            {paymentStatus === 'pending' ?
                                (language === "en" ? "Payment in" : "Thanh toán trong") :
                                (language === "en" ? "Payment Status" : "Trạng thái TT")}
                        </h3>
                        {paymentStatus === 'pending' && !hasNavigatedOrTimedOutRef.current && (
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
                        <p className="text-gray-500 h-48 flex items-center justify-center">
                            {/* Thông báo lỗi khi không tạo được QR sẽ nằm trong statusMessage */}
                            {paymentStatus === 'initializing' && (language === "en" ? "Generating QR Code..." : "Đang tạo mã QR...")}
                        </p>
                    )}
                    <p className="mt-4 text-sm text-gray-600 leading-tight">
                        {language === "en" ? "Scan QR to pay" : "Quét mã QR để thanh toán"}
                        <br />
                        {language === "en" ? "Account Holder: " : "Chủ tài khoản: "}<b>{MY_ACCOUNT_HOLDER}</b>
                        <br />
                        {language === "en" ? "Bank: " : "Ngân hàng: "}<b>MB Bank</b>
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


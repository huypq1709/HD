import React, { useEffect, useState, useRef, useCallback } from "react";
import { Slogan } from "./Slogan";
// import Loader from "./Loader"; // Nếu bạn có loader

interface PaymentScreenProps {
    formData: {
        service: string;
        membership: string;
        phoneNumber: string;
        [key: string]: any;
    };
    nextStep: () => void; // Hàm để chuyển sang ConfirmationScreen (step 7)
    prevStep: () => void;
    language: string;
    resetToIntro: () => void;
    resetFormData: () => void;
}

const MY_BANK_ACCOUNT = "07019218501";
const MY_BANK_NAME_VIETQR_ID = "TPB"; // TPBank
const MY_ACCOUNT_HOLDER = "PHAM QUANG HUY";
const PAYMENT_UI_TIMEOUT_SECONDS = 120; // 2 phút

export function PaymentScreen({
                                  formData,
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
        // Chỉ chạy nếu chưa có orderId và chưa điều hướng/timeout
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
                        }),
                    });
                    const data = await response.json();
                    if (response.ok && data.success && data.order_id && data.expected_amount && data.payment_message) {
                        setPaymentDetails({
                            orderId: data.order_id,
                            expectedAmount: data.expected_amount,
                            paymentMessage: data.payment_message,
                        });
                        const qrUrl = `https://qr.sepay.vn/img?acc=${MY_BANK_ACCOUNT}&bank=${MY_BANK_NAME_VIETQR_ID}&amount=${data.expected_amount}&des=${encodeURIComponent(data.payment_message)}&template=compact2`;
                        setQrCodeUrl(qrUrl);
                        setPaymentStatus("pending"); // Chuyển sang chờ thanh toán
                    } else {
                        throw new Error(data.message || "Failed to start payment session.");
                    }
                } catch (error: any) {
                    console.error("Error initiating payment session:", error);
                    setPaymentStatus("error_session"); // Lỗi khi khởi tạo
                }
            };
            initiateAndGenerateQR();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Chạy một lần khi component mount

    // EFFECT 2: Polling kiểm tra trạng thái
    useEffect(() => {
        if (paymentDetails.orderId && paymentStatus === "pending" && !hasNavigatedOrTimedOutRef.current) {
            if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
            
            // Polling ngay lập tức lần đầu
            const checkStatus = async () => {
                try {
                    const response = await fetch(`/api/app1/check-payment-status?order_id=${paymentDetails.orderId}`);
                    const result = await response.json();
                    console.log("Polling result for order", paymentDetails.orderId, ":", result);
                    
                    if (result.success) {
                        if (result.status === "success") {
                            setPaymentStatus("success");
                            stopPolling();
                            stopTimer();
                            hasNavigatedOrTimedOutRef.current = true;
                            setTimeout(() => {
                                nextStep();
                            }, 2000);
                        } else if (result.status === "failed_amount_mismatch") {
                            setPaymentStatus("failed_amount_mismatch");
                            stopPolling();
                            stopTimer();
                        } else if (result.status === "timeout") {
                            setPaymentStatus("timeout");
                            stopPolling();
                            stopTimer();
                            hasNavigatedOrTimedOutRef.current = true;
                            resetFormData();
                            setTimeout(() => {
                                resetToIntro();
                            }, 3000);
                        } else if (result.status === "not_found") {
                            setPaymentStatus("error_polling");
                            stopPolling();
                            stopTimer();
                        }
                    }
                } catch (error) {
                    console.error("Polling error:", error);
                    setPaymentStatus("error_polling");
                    stopPolling();
                    stopTimer();
                }
            };

            // Chạy kiểm tra ngay lập tức
            checkStatus();
            
            // Sau đó mới bắt đầu polling mỗi 2 giây
            pollingIntervalRef.current = setInterval(checkStatus, 2000);
        }
        return () => stopPolling();
    }, [paymentDetails.orderId, paymentStatus, stopPolling, stopTimer, nextStep, resetToIntro, resetFormData]);

    // EFFECT 3: Bộ đếm ngược thời gian
    useEffect(() => {
        if (paymentStatus === 'pending' && !hasNavigatedOrTimedOutRef.current) {
            if (timeLeft === 0) {
                stopTimer();
                setPaymentStatus("timeout_ui");
                hasNavigatedOrTimedOutRef.current = true;
                resetFormData();
                setTimeout(() => {
                    resetToIntro();
                }, 3000);
                return;
            }
            timerIntervalRef.current = setInterval(() => {
                setTimeLeft((prevTime) => (prevTime > 0 ? prevTime - 1 : 0));
            }, 1000);
        } else {
            stopTimer();
        }
        return () => stopTimer();
    }, [timeLeft, paymentStatus, stopTimer, resetToIntro, resetFormData]);

    // EFFECT 4: Xử lý logic dựa trên thay đổi paymentStatus
    useEffect(() => {
        if (hasNavigatedOrTimedOutRef.current) return;

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
                break;
            case "failed_amount_mismatch":
                newMessage = language === "en" ? "Payment failed: Amount mismatch. Contact support." : "Thanh toán thất bại: Sai số tiền. Vui lòng liên hệ hỗ trợ.";
                shouldStopActivities = true;
                break;
            case "timeout_ui":
            case "timeout":
                newMessage = language === "en" ? "Payment timed out. Returning to home..." : "Hết thời gian thanh toán. Đang quay về trang chủ...";
                shouldStopActivities = true;
                break;
            case "error_session":
                newMessage = language === "en" ? "Error initializing. Please try again or go back." : "Lỗi khởi tạo phiên. Vui lòng thử lại hoặc quay lại.";
                shouldStopActivities = true;
                break;
            case "error_polling":
                newMessage = language === "en" ? "Could not check payment status. Please check your connection or go back." : "Không thể kiểm tra trạng thái thanh toán. Vui lòng kiểm tra kết nối hoặc quay lại.";
                shouldStopActivities = true;
                break;
            default:
                return;
        }

        setStatusMessage(newMessage);

        if (shouldStopActivities) {
            stopPolling();
            stopTimer();
        }
    }, [paymentStatus, language, stopPolling, stopTimer]);


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

// export default PaymentScreen; // Nếu bạn dùng file riêng
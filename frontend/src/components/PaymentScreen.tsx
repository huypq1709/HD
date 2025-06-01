import React, { useEffect, useState, useRef } from "react";
import { Slogan } from "./Slogan";

// Định nghĩa lại các props cho rõ ràng
interface PaymentScreenProps {
    formData: {
        service: string;
        membership: string;
        phoneNumber: string;
        membershipPriceFormatted?: string;
        [key: string]: any;
    };
    nextStep: () => void;
    prevStep: () => void;
    language: string;
    resetToIntro: () => void;
    resetFormData: () => void;
}

export function PaymentScreen({
                                  formData,
                                  nextStep,
                                  prevStep,
                                  language,
                                  resetToIntro,
                                  resetFormData,
                              }: PaymentScreenProps) {
    // --- STATE MANAGEMENT ---
    const [timeLeft, setTimeLeft] = useState(120); // Đếm ngược 2 phút
    const [paymentStatus, setPaymentStatus] = useState<string>("initializing"); // Trạng thái thanh toán: initializing, pending, success, timeout, error
    const [statusMessage, setStatusMessage] = useState<string>(
        language === "en" ? "Initializing payment session..." : "Đang khởi tạo phiên thanh toán..."
    );
    // Lưu số tiền cần thanh toán từ backend để dùng cho việc polling
    const [expectedAmount, setExpectedAmount] = useState<number | null>(null);

    // Ref để đảm bảo các hành động chỉ chạy một lần
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const hasNavigatedRef = useRef(false); // Ref để chống gọi nextStep/resetToIntro nhiều lần

    // --- LOGIC HELPER ---
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    const displayPrice = formData.membershipPriceFormatted || "N/A";

    // --- EFFECT 1: BẮT ĐẦU PHIÊN THANH TOÁN KHI COMPONENT MOUNT ---
    useEffect(() => {
        const startPaymentSession = async () => {
            try {
                // Gọi API backend để tạo phiên thanh toán
                const response = await fetch("http://localhost:5001/start-payment-session", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        service: formData.service,
                        membership: formData.membership,
                        phoneNumber: formData.phoneNumber,
                    }),
                });

                const data = await response.json();

                if (response.ok && data.status === "session_started") {
                    console.log("Backend response (Session Started):", data);
                    setExpectedAmount(data.expected_amount); // Lưu lại số tiền cần thanh toán
                    setPaymentStatus("pending"); // Chuyển sang trạng thái chờ
                    setStatusMessage(language === "en" ? "Waiting for payment..." : "Đang chờ thanh toán...");
                } else {
                    throw new Error(data.message || "Failed to start session.");
                }
            } catch (error) {
                console.error("Failed to start payment session:", error);
                setPaymentStatus("error");
                setStatusMessage(language === "en" ? "Error starting payment session." : "Lỗi khi bắt đầu phiên thanh toán.");
            }
        };

        startPaymentSession();
    }, [formData, language]); // Chạy một lần khi component mount

    // --- EFFECT 2: BẮT ĐẦU POLLING KHI CÓ PHIÊN THANH TOÁN ---
    useEffect(() => {
        // Chỉ bắt đầu polling khi có expectedAmount và trạng thái đang là pending
        if (expectedAmount !== null && paymentStatus === "pending") {
            pollingIntervalRef.current = setInterval(async () => {
                try {
                    // Gọi API kiểm tra trạng thái định kỳ mỗi 2 giây
                    const response = await fetch(`http://localhost:5001/check-payment-status?expected_amount=${expectedAmount}`);
                    const result = await response.json();
                    console.log("Polling for status:", result);

                    // Nếu trạng thái không còn là "pending", cập nhật state và dừng polling
                    if (result.status !== "pending" && result.status !== "not_found") {
                        setPaymentStatus(result.status); // Cập nhật trạng thái cuối cùng (success, timeout, fail_amount_mismatch)
                    }
                } catch (error) {
                    console.error("Polling failed:", error);
                    // Có thể tạm dừng polling nếu có lỗi mạng
                }
            }, 2000); // Polling mỗi 2 giây
        }

        // Cleanup: Dọn dẹp interval khi component unmount hoặc khi trạng thái thay đổi
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
        };
    }, [expectedAmount, paymentStatus, language]); // Phụ thuộc vào các giá trị này

    // --- EFFECT 3: XỬ LÝ KHI TRẠNG THÁI THANH TOÁN THAY ĐỔI ---
    useEffect(() => {
        if (hasNavigatedRef.current) return; // Nếu đã điều hướng thì không làm gì nữa

        // Dừng polling ngay lập tức nếu trạng thái không còn là pending
        if (paymentStatus !== 'pending' && pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
        }

        if (paymentStatus === "success") {
            hasNavigatedRef.current = true;
            setStatusMessage(language === "en" ? "Payment successful! Redirecting..." : "Thanh toán thành công! Đang chuyển hướng...");
            setTimeout(() => {
                nextStep(); // Chuyển đến màn hình xác nhận
            }, 1500); // Chờ 1.5 giây để người dùng đọc thông báo
        } else if (paymentStatus === "fail_amount_mismatch") {
            setStatusMessage(language === "en" ? "Payment failed: Amount mismatch." : "Thanh toán thất bại: Sai số tiền.");
        } else if (paymentStatus === "timeout") {
            setStatusMessage(language === "en" ? "Payment timed out. Please try again." : "Hết thời gian thanh toán. Vui lòng thử lại.");
            // Bộ đếm thời gian sẽ xử lý việc quay về trang chủ
        }
    }, [paymentStatus, language, nextStep]);


    // --- EFFECT 4: BỘ ĐẾM NGƯỢC THỜI GIAN ---
    useEffect(() => {
        if (timeLeft === 0 && paymentStatus === 'pending') {
            if (!hasNavigatedRef.current) {
                hasNavigatedRef.current = true;
                setStatusMessage(language === "en" ? "Time expired. Returning to home..." : "Hết thời gian. Đang quay về trang chủ...");
                resetFormData();
                localStorage.removeItem("phoneNumber");
                setTimeout(() => {
                    resetToIntro();
                }, 2000);
            }
            return;
        }

        const timer = setInterval(() => {
            setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);

        return () => clearInterval(timer);
    }, [timeLeft, resetFormData, resetToIntro, language, paymentStatus]);


    // --- RENDER COMPONENT ---
    const getMembershipNameDisplay = (membershipId: string, lang: string) => {
        const names: { [key: string]: { en: string; vi: string } } = {
            "1 day": { en: "1 Day Pass", vi: "Gói 1 Ngày" },
            "1 month": { en: "1 Month Pass", vi: "Gói 1 Tháng" },
            // thêm các gói khác...
        };
        return names[membershipId]?.[lang as "en" | "vi"] || membershipId;
    };

    const cleanServiceName = (rawService: string) => rawService.replace(/\s*\(.*?\)/g, "").trim();

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
                    <span className="font-semibold">{displayPrice}</span>
                </div>
            </div>

            <div className="flex space-x-4">
                <div className="w-1/2 text-center p-6 border-2 border-dashed border-gray-300 rounded-lg">
                    <h3 className="text-2xl font-semibold text-gray-800">{language === "en" ? "Payment in" : "Thanh toán trong"}</h3>
                    <p className="mt-2 text-6xl font-bold text-red-500">{minutes}:{seconds < 10 ? `0${seconds}` : seconds}</p>
                    {/* Hiển thị thông báo trạng thái */}
                    <p className="mt-4 text-lg font-medium text-blue-600 h-10">{statusMessage}</p>
                </div>

                <div className="w-1/2 text-center p-6 border-2 border-dashed border-gray-300 rounded-lg">
                    <img src="/qr.jpg" alt="QR Code" className="h-48 w-48 mx-auto object-contain" />
                    <p className="mt-4 text-gray-600">
                        {language === "en" ? "Scan QR to pay" : "Quét mã QR để thanh toán"}
                        <br />
                        <b>CAO THI HOA</b>
                        <br />
                        <b>0288639397979</b>
                    </p>
                </div>
            </div>

            <div className="flex justify-start pt-4">
                <button
                    onClick={prevStep}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                    disabled={paymentStatus !== 'initializing' && paymentStatus !== 'pending'} // Vô hiệu hóa nút khi đang xử lý
                >
                    {language === "en" ? "Back" : "Quay lại"}
                </button>
            </div>

            <Slogan message={language === "en" ? "Maintain cleanliness and hygiene." : "Duy trì vệ sinh và sạch sẽ."} language={language} />
        </div>
    );
}

export default PaymentScreen;
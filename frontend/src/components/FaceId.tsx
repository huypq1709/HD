import { useEffect, useState } from "react";
import Loader from "./Loader";

interface FaceIdProps {
    checkUserInfo: (phone: string) => Promise<{ name: string; phone: string; status: string } | null>;
    resetToIntro: () => void;
    language: string;
}

export function FaceId({ checkUserInfo, resetToIntro, language }: FaceIdProps) {
    const [phoneNumber, setPhoneNumber] = useState("");
    const [customerInfo, setCustomerInfo] = useState<{ name: string; phone: string; status: string } | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [redirectCountdown, setRedirectCountdown] = useState(30);
    const [verificationCountdown, setVerificationCountdown] = useState<number | null>(null);
    const [notFound, setNotFound] = useState(false);
    const [fetchError, setFetchError] = useState(false);
    const [registrationCompleted, setRegistrationCompleted] = useState(false); // Theo dõi trạng thái đăng ký

    useEffect(() => {
        if(registrationCompleted){
            const utterance = new SpeechSynthesisUtterance();
            utterance.rate = 0.65;

            if (language == "en"){
                utterance.text = "Face ID registration completed successfully!";
                utterance.lang = "en-US";
            } else {
                utterance.text = "Cập nhật khuôn mặt thành công"
                utterance.lang = "vi-VN";
            }

            speechSynthesis.speak(utterance);
        }
    }, [registrationCompleted, language]);

    useEffect(() => {
        if (loading) {
            setVerificationCountdown(40);
            const intervalId = setInterval(() => {
                setVerificationCountdown((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
            }, 1000);
            return () => clearInterval(intervalId);
        } else {
            setVerificationCountdown(null);
        }
    }, [loading]);

    const handleCheck = async () => {
        if (!/^\d{10}$/.test(phoneNumber)) {
            setError(
                language === "en"
                    ? "Please enter a valid 10-digit phone number."
                    : "Vui lòng nhập số điện thoại 10 chữ số."
            );
            return;
        }
        setLoading(true);
        setError("");
        setNotFound(false);
        setFetchError(false);
        setRegistrationCompleted(false); // Reset trạng thái đăng ký

        try {
            const data = await checkUserInfo(phoneNumber);
            setCustomerInfo(data);
            if (data && data.status === "not_found") {
                setNotFound(true);
            } else if (data && data.status === "face_registration_completed") {
                setRegistrationCompleted(true);
                // Có thể cập nhật customerInfo nếu API trả về thông tin mới sau đăng ký
            }
        } catch (err: any) {
            setError(err.message);
            setFetchError(true);
            setNotFound(true);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        let timer: NodeJS.Timeout;
        if (customerInfo || notFound || fetchError || registrationCompleted) {
            timer = setInterval(() => {
                setRedirectCountdown((prev) => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        setPhoneNumber("");
                        setCustomerInfo(null);
                        setRegistrationCompleted(false);
                        localStorage.removeItem("phoneNumber");
                        resetToIntro();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [customerInfo, resetToIntro, notFound, fetchError, registrationCompleted]);

    return (
        <div className="space-y-6 p-4">
            <h2 className="text-2xl font-semibold text-gray-800">
                {language === "en" ? "Update FaceId" : "Cập nhật Face ID"}
            </h2>
            <p className="text-gray-600">
                {language === "en"
                    ? "Enter your phone number to retrieve your information for Face ID update. (Only available for customers with active packages)"
                    : "Nhập số điện thoại của bạn để lấy thông tin cập nhật Face ID. (Chỉ áp dụng với khách có gói đang hoạt động)"}
            </p>
            <input
                type="tel"
                maxLength={10}
                pattern="\d{10}"
                value={phoneNumber}
                onChange={(e) => {
                    setPhoneNumber(e.target.value);
                    localStorage.setItem("phoneNumber", e.target.value);
                }}
                placeholder={language === "en" ? "10-digit Phone Number" : "Số điện thoại 10 chữ số"}
                className="border p-2 rounded w-full"
            />
            <button
                onClick={handleCheck}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
                {language === "en" ? "Update" : "Cập nhật"}
            </button>
            {loading && (
                <div className="flex flex-col justify-center items-center">
                    <Loader />
                    <span className="mt-2 text-gray-600">
                        {language === "en"
                            ? `Please move to camera and look straight ahead for ${verificationCountdown !== null ? verificationCountdown : '...' } seconds`
                            : `Quý khách di chuyển sang vị trí camera và nhìn thẳng trong ${verificationCountdown !== null ? verificationCountdown : '...' } giây`}
                    </span>
                </div>
            )}

            {error && !fetchError && <p className="text-red-500">{error}</p>}

            {(customerInfo && customerInfo.status === "found") || registrationCompleted ? (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">
                        {language === "en" ? "Customer Information" : "Thông Tin Khách Hàng"}
                    </h3>
                    <p className="text-gray-600">
                        {language === "en" ? "Name" : "Họ và tên"}: <span className="font-medium">{customerInfo?.name}</span>
                    </p>
                    <p className="text-gray-600">
                        {language === "en" ? "Phone Number" : "Số điện thoại"}: <span className="font-medium">{customerInfo?.phone}</span>
                    </p>
                    {registrationCompleted && (
                        <p className="text-green-500 mt-2 text-center">
                            {language === "en" ? "Face ID registration completed successfully!" : "Đăng ký Face ID thành công!"}
                        </p>
                    )}
                    <p className="mt-2 text-gray-500 text-center">
                        {language === "en"
                            ? `You will be redirected to Home automatically in ${redirectCountdown} second${redirectCountdown === 1 ? "" : "s"}.`
                            : `Bạn sẽ được chuyển về Trang Chủ tự động sau ${redirectCountdown} giây.`}
                    </p>
                </div>
            ) : null}

            {(notFound || fetchError) && (
                <div className="bg-white rounded-lg shadow-md p-6">
                    <p className="text-gray-700 text-center">
                        {language === "en"
                            ? "No customer information found. Please double-check your phone number."
                            : "Không tìm thấy thông tin khách hàng. Vui lòng kiểm tra lại số điện thoại."}
                    </p>
                    <p className="mt-2 text-gray-500 text-center">
                        {language === "en"
                            ? `You will be redirected to Home automatically in ${redirectCountdown} second${redirectCountdown === 1 ? "" : "s"}.`
                            : `Bạn sẽ được chuyển về Trang Chủ tự động sau ${redirectCountdown} giây.`}
                    </p>
                </div>
            )}

            <div className="flex justify-center mt-6">
                <button
                    onClick={resetToIntro}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded"
                >
                    {language === "en" ? "Back to Home" : "Quay lại Trang Chủ"}
                </button>
            </div>
        </div>
    );
}
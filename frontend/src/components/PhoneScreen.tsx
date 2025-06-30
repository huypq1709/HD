import React, { useState, useEffect } from "react";
import Loader from "./Loader"; // Đảm bảo đường dẫn đến component Loader của bạn là đúng
import { playSound, stopSound } from "../utils/playSound";

interface PhoneScreenProps {
    formData: {
        customerType: string;
        fullName: string;
        phoneNumber: string;
        service: string;
        membership: string;
    };
    updateFormData: (field: string, value: any) => void;
    nextStep: () => void;
    prevStep: () => void;
    language: string;
    processPhoneNumber: (phone: string) => Promise<'found' | 'not_found' | 'error'>;
    resetToIntro: () => void;
}

export function PhoneScreen({
                                formData,
                                updateFormData,
                                nextStep,
                                prevStep,
                                language,
                                processPhoneNumber,
                                resetToIntro,
                            }: PhoneScreenProps) {
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [countdown, setCountdown] = useState<number | null>(null);

    const validatePhone = (phone: string) => {
        return phone.trim().length >= 10;
    };

    useEffect(() => {
        if (loading) {
            setCountdown(30);
            const intervalId = setInterval(() => {
                setCountdown((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
            }, 1000);
            return () => clearInterval(intervalId);
        } else {
            setCountdown(null);
        }
    }, [loading]);

    useEffect(() => {
        playSound(3, language);
        return () => { stopSound(); };
    }, [language]);

    useEffect(() => {
        if (typeof error === 'string' && error && (
            error.toLowerCase().includes("lỗi") ||
            error.toLowerCase().includes("thất bại") ||
            error.toLowerCase().includes("error") ||
            error.toLowerCase().includes("failed")
        )) {
            const timer = setTimeout(() => {
                window.location.reload();
                if (typeof resetToIntro === 'function') resetToIntro();
            }, 60000);
            return () => clearTimeout(timer);
        }
    }, [error, resetToIntro]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!validatePhone(formData.phoneNumber)) {
            setError(
                language === "en"
                    ? "Please enter a valid 10-digit phone number."
                    : "Vui lòng nhập số điện thoại 10 chữ số."
            );
            return;
        }

        setLoading(true);
        setError("");

        try {
            const result = await processPhoneNumber(formData.phoneNumber);
            setLoading(false);

            if (formData.customerType === "new") {
                if (result === 'found') {
                    setError(
                        language === "en"
                            ? "This phone number already exists. Please go back and select 'Returning Customer' to renew."
                            : "Số điện thoại này đã tồn tại. Vui lòng quay lại và chọn 'Khách hàng cũ' để gia hạn."
                    );
                } else if (result === 'not_found') {
                    nextStep();
                } else {
                    setError(
                        language === "en"
                            ? "Error checking information."
                            : "Lỗi trong quá trình kiểm tra thông tin."
                    );
                }
            } else if (formData.customerType === "returning") {
                if (result === 'found') {
                    nextStep();
                } else if (result === 'not_found') {
                    setError(
                        language === "en"
                            ? "This phone number is not registered. Please go back and select 'New Customer' to register."
                            : "Số điện thoại này chưa được đăng ký. Vui lòng quay lại và chọn 'Khách hàng mới' để đăng ký."
                    );
                } else {
                    setError(
                        language === "en"
                            ? "Error checking information."
                            : "Lỗi trong quá trình kiểm tra thông tin."
                    );
                }
            }
        } catch (error: any) {
            console.error('Lỗi processPhoneNumber:', error);
            setError(error.message || "Đã có lỗi xảy ra trong quá trình xử lý.");
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
                {language === "en" ? "Phone Number" : "Số Điện Thoại"}
            </h2>
            <p className="text-gray-600">
                {language === "en"
                    ? "Please enter your contact number"
                    : "Vui lòng nhập số điện thoại liên hệ của bạn"}
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 mb-1">
                        {language === "en" ? "Phone Number" : "Số Điện Thoại"}
                    </label>
                    <input
                        type="tel"
                        id="phoneNumber"
                        value={formData.phoneNumber}
                        onChange={(e) => {
                            updateFormData("phoneNumber", e.target.value);
                            setError("");
                        }}
                        className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none ${
                            error ? "border-red-500" : "border-gray-300"
                        }`}
                        placeholder="(123) 456-7890"
                    />
                    {error && !loading && <p className="mt-1 text-sm text-red-600">{error}</p>}
                </div>

                {loading && (
                    <div className="flex flex-col items-center pt-4">
                        <Loader />
                        <p className="mt-2 text-sm text-gray-600">
                            {language === "en"
                                ? `Verifying information in ${countdown !== null ? countdown : '...' } seconds. Let's warm up a bit!`
                                : `Đang xác minh thông tin trong ${countdown !== null ? countdown : '...' } giây. Hãy khởi động một chút nào!`}
                        </p>
                    </div>
                )}

                <div className="flex justify-between pt-4">
                    <button
                        type="button"
                        onClick={prevStep}
                        className={`px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        disabled={loading}
                    >
                        {language === "en" ? "Back" : "Quay lại"}
                    </button>
                    {!loading && !error && (
                        <button
                            type="submit"
                            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {language === "en" ? "Next" : "Tiếp tục"}
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
}
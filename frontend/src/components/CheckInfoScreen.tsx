import { useEffect, useState } from "react";
import Loader from "./Loader";

interface CheckInfoScreenProps {
    checkUserInfo: (phone: string) => Promise<any>;
    resetToIntro: () => void;
    language: string;
}

export function CheckInfoScreen({ checkUserInfo, resetToIntro, language }: CheckInfoScreenProps) {
    const [phoneNumber, setPhoneNumber] = useState("");
    const [info, setInfo] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [redirectCountdown, setRedirectCountdown] = useState(30);
    const [verificationCountdown, setVerificationCountdown] = useState<number | null>(null);
    const [noRecords, setNoRecords] = useState(false);
    const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
    const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

    // Hàm để kiểm tra trạng thái task
    const checkTaskStatus = async (taskId: string) => {
        try {
            const response = await fetch(`http://localhost:5000/start-check-info/${taskId}`);
            const data = await response.json();

            if (data.status === "completed") {
                // Dừng polling
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                    setPollingInterval(null);
                }
                setLoading(false);
                setInfo(data.data);
                if (data.data.results && data.data.results.length === 0) {
                    setNoRecords(true);
                }
            } else if (data.status === "error") {
                // Dừng polling và hiển thị lỗi
                if (pollingInterval) {
                    clearInterval(pollingInterval);
                    setPollingInterval(null);
                }
                setLoading(false);
                setError(data.error || (language === "en" ? "An error occurred" : "Đã xảy ra lỗi"));
                setNoRecords(true);
            }
            // Nếu status là "pending" hoặc "processing", tiếp tục polling
        } catch (err: any) {
            // Dừng polling nếu có lỗi
            if (pollingInterval) {
                clearInterval(pollingInterval);
                setPollingInterval(null);
            }
            setLoading(false);
            setError(err.message);
            setNoRecords(true);
        }
    };

    // Cleanup polling interval khi component unmount
    useEffect(() => {
        return () => {
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
        };
    }, [pollingInterval]);

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
        setNoRecords(false);
        setInfo(null);

        try {
            // Gọi API để bắt đầu task
            const response = await checkUserInfo(phoneNumber);
            if (response.task_id) {
                setCurrentTaskId(response.task_id);
                // Bắt đầu polling mỗi 2 giây
                const interval = setInterval(() => checkTaskStatus(response.task_id), 2000);
                setPollingInterval(interval);
            } else {
                throw new Error(language === "en" ? "Failed to start task" : "Không thể bắt đầu tác vụ");
            }
        } catch (err: any) {
            setLoading(false);
            setError(err.message);
            setNoRecords(true);
        }
    };

    useEffect(() => {
        if (loading) {
            setVerificationCountdown(30);
            const intervalId = setInterval(() => {
                setVerificationCountdown((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
            }, 1000);
            return () => clearInterval(intervalId);
        } else {
            setVerificationCountdown(null);
        }
    }, [loading]);

    useEffect(() => {
        let timer: NodeJS.Timeout;
        if ((info && info.results && info.results.length > 0) || noRecords) {
            timer = setInterval(() => {
                setRedirectCountdown((prev) => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        setPhoneNumber("");
                        localStorage.removeItem("phoneNumber");
                        resetToIntro();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        return () => clearInterval(timer);
    }, [info, resetToIntro, noRecords]);

    return (
        <div className="space-y-6 p-4">
            <h2 className="text-2xl font-semibold text-gray-800">
                {language === "en" ? "Check Information" : "Kiểm Tra Thông Tin"}
            </h2>
            <p className="text-gray-600">
                {language === "en"
                    ? "Enter your 10-digit phone number to check your membership information."
                    : "Nhập số điện thoại 10 chữ số của bạn để kiểm tra thông tin thành viên."}
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
                disabled={loading}
                className={`w-full px-4 py-2 ${loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'} text-white rounded`}
            >
                {loading 
                    ? (language === "en" ? "Checking..." : "Đang kiểm tra...")
                    : (language === "en" ? "Check" : "Kiểm Tra")}
            </button>
            {loading && (
                <div className="flex flex-col justify-center items-center">
                    <Loader />
                    <span className="mt-2 text-gray-600">
                        {language === "en"
                            ? `Verifying information in ${verificationCountdown !== null ? verificationCountdown : '...' } seconds`
                            : `Đang xác minh thông tin trong ${verificationCountdown !== null ? verificationCountdown : '...' } giây`}
                    </span>
                </div>
            )}

            {error && <p className="text-red-500">{error}</p>}
            {info && (info.results && info.results.length > 0 ? (
                <div className="bg-white rounded-lg shadow-md">
                    <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                            <thead className="bg-gray-100 text-gray-700 text-sm">
                            <tr>
                                <th className="px-6 py-3 text-left font-semibold text-[12px] tracking-wider">Name</th>
                                <th className="px-6 py-3 text-left font-semibold text-[12px] tracking-wider">Service</th>
                                <th className="px-6 py-3 text-left font-semibold text-[12px] tracking-wider">Start Date</th>
                                <th className="px-6 py-3 text-left font-semibold text-[12px] tracking-wider">End Date</th>
                                <th className="px-6 py-3 text-left font-semibold text-[12px] tracking-wider">Remaining</th>
                                <th className="px-6 py-3 text-left font-semibold text-[12px] tracking-wider">Status</th>
                            </tr>
                            </thead>
                            <tbody>
                            {info.results.map((item: any, index: number) => (
                                <tr key={index} className="border-b hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-[12px] font-medium text-gray-900">{item.name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-[12px] text-gray-700">{item.service?.replace(/\s*\(.*?\)/g, '')}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-[12px] text-gray-700">{item.start_date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-[12px] text-gray-700">{item.end_date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-[12px]"><span
                                        className="font-medium text-green-600">{item.remaining}</span></td>
                                    <td className="px-6 py-4 whitespace-nowrap  ">
                                        {item.status === "Hết hạn" ? (
                                            <span className="inline-flex text-[12px] items-center px-2 py-1 rounded-full font-medium bg-red-100 text-red-800">
      <svg className="w-3 h-3 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"> <circle
          cx="12" cy="12" r="10"></circle> <line x1="12" y1="8" x2="12" y2="12"></line> <line x1="12" y1="16" x2="12.01"
                                                                                              y2="16"></line> </svg>
                                                {item.status}
    </span>
                                        ) : item.status === "Đang hoạt động" ? (
                                            <span
                                                className="text-[12px] inline-flex items-center px-2 py-1 rounded-full font-medium bg-green-100 text-green-800">
      <svg className="w-3 h-3 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="20 6 9 17 4 12"></polyline>
      </svg>
                                                {item.status}
    </span>
                                        ) : (
                                            <span className="text-xs text-gray-500">{item.status}</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                    <p className="mt-2 text-gray-500 text-center">
                        {language === "en"
                            ? `You will be redirected to Home automatically in ${redirectCountdown} second${redirectCountdown === 1 ? "" : "s"}.`
                            : `Bạn sẽ được chuyển về Trang Chủ tự động sau ${redirectCountdown} giây.`}
                    </p>
                </div>
            ) : noRecords ? (
                <div className="bg-white rounded-lg shadow-md">
                    <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                            <thead>
                            <tr className="bg-gray-100 text-gray-700 text-sm">
                                <th className="px-6 py-3 text-left font-semibold text-[12px] tracking-wider" colSpan={6}>
                                    {language === "en" ? "No records found" : "Không tìm thấy bản ghi nào"}
                                </th>
                            </tr>
                            </thead>
                            <tbody>
                            <tr>
                                <td colSpan={6} className="px-6 py-4 text-center text-gray-700">
                                    {language === "en" ? "No customer information found." : "Không tìm thấy thông tin khách hàng."}
                                </td>
                            </tr>
                            </tbody>
                        </table>
                    </div>
                    <p className="mt-2 text-gray-500 text-center">
                        {language === "en"
                            ? `You will be redirected to Home automatically in ${redirectCountdown} second${redirectCountdown === 1 ? "" : "s"}.`
                            : `Bạn sẽ được chuyển về Trang Chủ tự động sau ${redirectCountdown} giây.`}
                    </p>
                </div>
            ) : null)}
            <div className="flex justify-center">
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
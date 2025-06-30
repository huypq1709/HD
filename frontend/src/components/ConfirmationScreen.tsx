import React, { useState, useEffect, useRef, useCallback } from 'react';
import { registerUser } from '../api/registration'; // Đảm bảo hàm này gọi đúng '/api/app5/start-automation'
import Loader from './Loader'; // Component Loader của bạn
import { Slogan } from './Slogan'; // Component Slogan của bạn
import { playSound, stopSound } from "../utils/playSound";

interface ConfirmationScreenProps {
  formData: {
    customerType: string;
    fullName: string;
    phoneNumber: string;
    service: string;
    membership: string;
    [key: string]: any;
  };
  updateFormData: (field: string, value: any) => void;
  nextStep: () => void; // Chuyển sang FaceID cho khách mới
  language: string;
  resetToIntro: () => void; // Quay về màn hình giới thiệu
}

export function ConfirmationScreen({ formData, updateFormData, nextStep, language, resetToIntro }: ConfirmationScreenProps) {
  const [isProcessing, setIsProcessing] = useState(true); // Trạng thái chung cho việc đang xử lý
  const [processMessage, setProcessMessage] = useState<string>(''); // Thông báo cho người dùng (đang xử lý, thành công, lỗi)
  const [countdown, setCountdown] = useState<number | null>(null); // Đếm ngược về Home cho khách cũ
  const [paymentStatus, setPaymentStatus] = useState<string>("initializing");
  const [showSummary, setShowSummary] = useState(false);
  const [processingCountdown, setProcessingCountdown] = useState<number | null>(null); // Đếm ngược khi đang xử lý

  const hasInitiatedProcessRef = useRef(false); // Đảm bảo chỉ chạy tự động hóa một lần
  const hasNavigatedRef = useRef(false);      // Đảm bảo chỉ điều hướng một lần

  // Hàm xử lý chính
  const runAutomationProcess = useCallback(async () => {
    if (hasInitiatedProcessRef.current) return; // Chỉ chạy một lần
    hasInitiatedProcessRef.current = true;

    setIsProcessing(true);
    setShowSummary(false);
    setProcessMessage(language === 'en' ? 'Processing your registration, please wait...' : 'Đang xử lý đăng ký của bạn, vui lòng chờ...');

    try {
      // Gọi API tự động hóa
      const result = await registerUser(formData); // Hàm này nằm trong api/registration.ts
      console.log('Automation API result:', result);

      if (result.status === 'success') {
        setShowSummary(true);
        if (formData.customerType === 'new' && result.final_action === 'redirect_faceid') {
          setProcessMessage(result.message || (language === 'en' ? 'Registration successful! Redirecting to Face ID setup...' : 'Đăng ký thành công! Đang chuyển đến cài đặt Face ID...'));
          const delay = (result.redirect_delay || 3) * 1000; // Mặc định 3 giây
          if (!hasNavigatedRef.current) {
            hasNavigatedRef.current = true;
            setTimeout(() => nextStep(), delay);
          }
        } else if (formData.customerType === 'returning' && result.final_action === 'return_home') {
          const delay = result.redirect_delay || 15; // Mặc định 15 giây
          setProcessMessage(result.message || (language === 'en' ? `Renewal successful! Returning to home screen in ${delay}s...` : `Gia hạn thành công! Quay về trang chủ sau ${delay} giây...`));
          setCountdown(delay); // Bắt đầu đếm ngược
        } else {
          // Trường hợp success nhưng không có action cụ thể hoặc customerType không khớp
          setProcessMessage(result.message || (language === 'en' ? 'Process completed successfully.' : 'Hoàn tất xử lý thành công.'));
          // Có thể bạn muốn tự động về home sau một lúc ở đây
          if (!hasNavigatedRef.current) { // Ví dụ, nếu là khách cũ nhưng backend không trả về return_home
            hasNavigatedRef.current = true;
            setTimeout(() => resetToIntro(), 15000);
          }
        }
      } else {
        // result.status === 'error' hoặc các trạng thái lỗi khác từ backend
        setProcessMessage(result.message || (language === 'en' ? 'Automation process failed. Please contact support.' : 'Quá trình tự động hóa thất bại. Vui lòng liên hệ hỗ trợ.'));
      }
    } catch (error: any) {
      // Lỗi từ hàm registerUser (ví dụ: Failed to fetch, hoặc lỗi ném ra từ registerUser)
      console.error('Error in runAutomationProcess:', error);
      setIsProcessing(false);
      setProcessMessage(error.message || (language === 'en' ? 'An error occurred. Please try again.' : 'Đã có lỗi xảy ra. Vui lòng thử lại.'));
    } finally {
      setIsProcessing(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData, language, nextStep, resetToIntro]); // Thêm các dependencies cần thiết

  // useEffect để chạy tự động hóa khi component mount
  useEffect(() => {
    runAutomationProcess();
  }, [runAutomationProcess]);

  // useEffect cho bộ đếm ngược về Home (chỉ khi countdown được set)
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (countdown !== null && countdown > 0 && !hasNavigatedRef.current) {
      setProcessMessage(language === 'en' ?
          `Membership renewed successfully! Returning to Home in ${countdown} seconds...` :
          `Gia hạn thành công! Quay về trang chủ sau ${countdown} giây...`);
      timer = setInterval(() => {
        setCountdown((prevTime) => (prevTime !== null ? prevTime - 1 : null));
      }, 1000);
    } else if (countdown === 0 && !hasNavigatedRef.current) {
      hasNavigatedRef.current = true;
      console.log("Countdown finished, resetting to intro screen.");
      resetToIntro();
    }
    return () => clearInterval(timer);
  }, [countdown, resetToIntro, language]);

  // useEffect: Nếu có lỗi hiển thị lên màn hình thì sau 60 giây sẽ reload lại và trở về Intro
  useEffect(() => {
    if (
      !isProcessing &&
      processMessage &&
      (
        processMessage.toLowerCase().includes("lỗi") ||
        processMessage.toLowerCase().includes("thất bại") ||
        processMessage.toLowerCase().includes("error") ||
        processMessage.toLowerCase().includes("failed")
      )
    ) {
      const timer = setTimeout(() => {
        window.location.reload();
        resetToIntro();
      }, 60000); // 60 giây
      return () => clearTimeout(timer);
    }
  }, [isProcessing, processMessage, resetToIntro]);

  useEffect(() => {
    playSound(7, language);
    return () => { stopSound(); };
  }, [language]);

  // useEffect cho bộ đếm ngược khi đang xử lý (60 giây)
  useEffect(() => {
    if (isProcessing) {
      setProcessingCountdown(60);
      const intervalId = setInterval(() => {
        setProcessingCountdown((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
      }, 1000);
      return () => clearInterval(intervalId);
    } else {
      setProcessingCountdown(null);
    }
  }, [isProcessing]);

  const getMembershipName = (id: string) => {
    const membershipsMap: { [key: string]: string } = {
      "1 day": language === "en" ? "1 Day" : "Gói 1 Ngày",
      "1 month": language === "en" ? "1 Month" : "Gói 1 Tháng",
      "3 months": language === "en" ? "3 Months" : "Gói 3 Tháng",
      "6 months": language === "en" ? "6 Months" : "Gói 6 Tháng",
      "1 year": language === "en" ? "1 Year" : "Gói 1 Năm",
    };
    return membershipsMap[id] || id;
  };

  return (
      <div className="space-y-6 p-4">
        <h2 className="text-2xl font-bold text-gray-900 text-center">
          {isProcessing ?
              (language === 'en' ? 'Processing Your Request' : 'Đang Xử Lý Yêu Cầu') :
              (language === 'en' ? 'Process Complete' : 'Hoàn Tất Xử Lý')}
        </h2>

        {/* Chỉ hiển thị thông tin tóm tắt khi không còn xử lý và có kết quả thành công */}
        {showSummary && !isProcessing && (
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <p className="text-center text-gray-700 text-lg mb-4">
              {language === 'en' ? 'Thank you! Here is your registration summary:' : 'Cảm ơn bạn! Đây là thông tin đăng ký của bạn:'}
            </p>
            <div className="text-gray-800 space-y-2">
              <p><strong>{language === 'en' ? 'Full Name:' : 'Họ và Tên:'}</strong> {formData.fullName}</p>
              <p><strong>{language === 'en' ? 'Phone Number:' : 'Số điện thoại:'}</strong> {formData.phoneNumber}</p>
              <p>
                <strong>{language === 'en' ? 'Service:' : 'Dịch vụ:'}</strong> {' '}
                {formData.service === 'gym' ? (language === 'en' ? 'Gym' : 'Gym') : (language === "en" ? 'Yoga' : 'Yoga')}
              </p>
              <p><strong>{language === 'en' ? 'Membership:' : 'Gói tập:'}</strong> {getMembershipName(formData.membership)}</p>
              <p>
                <strong>{language === 'en' ? 'Customer Type:' : 'Loại khách hàng:'}</strong> {' '}
                {formData.customerType === 'returning' ? (language === 'en' ? 'Returning' : 'Cũ') : (language === 'en' ? 'New' : 'Mới')}
              </p>
            </div>
          </div>
        )}

        {/* Hiển thị Loader và thông báo xử lý */}
        <div className="flex flex-col items-center mt-6 text-center">
          {isProcessing && <Loader />}
          <p className={`mt-4 text-lg ${processMessage.includes("Lỗi") || processMessage.includes("thất bại") || processMessage.includes("Error") || processMessage.includes("failed") ? 'text-red-600' : 'text-blue-600'}`}>
            {processMessage}
          </p>
          {isProcessing && (
            <span className="mt-2 text-gray-600">
              {language === "en"
                ? `Waiting for system response in ${processingCountdown !== null ? processingCountdown : '...'} seconds...`
                : `Đang chờ hệ thống phản hồi trong ${processingCountdown !== null ? processingCountdown : '...'} giây...`}
            </span>
          )}
        </div>

        {/* Nút quay về nếu có lỗi nghiêm trọng hoặc người dùng muốn quay lại sớm */}
        {(paymentStatus === "error_session" || paymentStatus === "error_polling" || (processMessage.includes("Lỗi") && !isProcessing)) && !hasNavigatedRef.current && (
            <div className="text-center mt-4">
              <button
                  onClick={resetToIntro}
                  className="px-6 py-2 text-white bg-red-500 rounded-md hover:bg-red-600"
              >
                {language === 'en' ? 'Return to Home' : 'Quay về Trang Chủ'}
              </button>
            </div>
        )}

        <div className="mt-8">
          <Slogan message={language === "en" ? "Your Wellness, Our Mission" : "Sức khỏe của bạn, sứ mệnh của chúng tôi"} language={language} />
        </div>
      </div>
  );
}

// export default ConfirmationScreen; // Bỏ comment nếu là file riêng
import { useState, useEffect } from 'react';
import { registerUser } from '../api/registration'; // Import hàm registerUser từ file riêng
import Loader from './Loader';

interface ConfirmationScreenProps {
  formData: {
    customerType: string;
    fullName: string;
    phoneNumber: string;
    service: string;
    membership: string;
    [key: string]: any;
  };
  updateFormData: (field: string, value: string) => void;
  nextStep: () => void; // Dùng để chuyển sang FaceID (khách mới)
  language: string;
  resetToIntro: () => void; // Thêm prop này để quay về màn hình giới thiệu
}

export function ConfirmationScreen({ formData, nextStep, language, resetToIntro }: ConfirmationScreenProps) {
  const [loadingRegistration, setLoadingRegistration] = useState(false);
  const [errorRegistration, setErrorRegistration] = useState<string>('');
  const [automationMessage, setAutomationMessage] = useState<string>('');
  const [automationComplete, setAutomationComplete] = useState(false);
  const [countdownToHome, setCountdownToHome] = useState<number | null>(null); // Bộ đếm ngược về Home

  // useEffect này sẽ chạy MỘT LẦN khi component mount
  // và kích hoạt toàn bộ quá trình tự động hóa
  useEffect(() => {
    // Chúng ta bắt đầu quá trình xử lý ngay khi màn hình xác nhận xuất hiện
    handleAutomationProcess();
  }, []); // [] đảm bảo chỉ chạy một lần khi component được render lần đầu

  // useEffect cho bộ đếm ngược về Home (chỉ khi là khách cũ và tự động hóa hoàn tất)
  useEffect(() => {
    let homeTimer: NodeJS.Timeout;
    if (countdownToHome !== null && countdownToHome > 0) {
      homeTimer = setInterval(() => {
        setCountdownToHome((prevTime) => (prevTime !== null ? prevTime - 1 : null));
      }, 1000);
    } else if (countdownToHome === 0) {
      // Khi bộ đếm về 0, quay về Home
      console.log("Countdown finished, resetting to intro screen.");
      resetToIntro(); // Gọi hàm resetToIntro được truyền từ App.tsx
    }
    return () => clearInterval(homeTimer); // Dọn dẹp timer khi component unmount hoặc dependency thay đổi
  }, [countdownToHome, resetToIntro]); // Thêm resetToIntro vào dependency array

  // Hàm chính xử lý toàn bộ quá trình: gọi API đăng ký/tự động hóa và quản lý trạng thái
  const handleAutomationProcess = async () => {
    setLoadingRegistration(true); // Bật trạng thái loading chung cho toàn bộ quá trình
    setErrorRegistration('');     // Reset lỗi
    setAutomationMessage(language === 'en' ? 'Processing registration and automation... Let\'s warm up a bit!' : 'Đang xử lý đăng ký và tự động hóa...Hãy khởi động một chút nhé!');
    setAutomationComplete(false); // Reset trạng thái hoàn thành

    try {
      // Gọi hàm registerUser từ file ../api/registration.ts
      // Hàm này sẽ gửi yêu cầu POST đến backend Flask trên cổng 5007
      const automationResult = await registerUser(formData);
      console.log('Automation result from backend:', automationResult);

      setLoadingRegistration(false); // Tắt loading sau khi nhận được phản hồi từ backend

      if (automationResult.status === 'success') {
        setAutomationComplete(true); // Đánh dấu quá trình tự động hóa đã hoàn thành thành công

        // Cập nhật thông báo dựa trên customerType
        if (formData.customerType === 'returning') {
          const redirectDelay = automationResult.redirect_delay || 5; // Mặc định 5 giây
          setCountdownToHome(redirectDelay);
          setAutomationMessage(language === 'en' ?
              `Membership renewed successfully! Returning to Home in ${redirectDelay} seconds...` :
              `Gia hạn thành công! Quay về trang chủ sau ${redirectDelay} giây...`);
        } else { // customerType === 'new'
          const redirectDelay = automationResult.redirect_delay || 5; // Mặc định 5 giây
          setAutomationMessage(language === 'en' ?
              'Registration complete! Redirecting to Face ID...' :
              'Đăng ký hoàn tất! Chuyển hướng đến Face ID...');
          setTimeout(() => {
            nextStep(); // Chuyển sang bước tiếp theo (FaceID)
          }, redirectDelay * 1000); // Chờ theo delay từ backend
        }
      } else {
        // Nếu backend trả về status là 'error'
        setErrorRegistration(language === 'en' ?
            `Automation failed: ${automationResult.message || 'Unknown error'}` :
            `Tự động hóa thất bại: ${automationResult.message || 'Lỗi không xác định'}`);
        setAutomationMessage(''); // Xóa thông báo tự động hóa nếu có lỗi
      }

    } catch (err: any) {
      // Bắt các lỗi xảy ra trong quá trình fetch (ví dụ: "Failed to fetch")
      console.error('Error during automation process:', err);
      setLoadingRegistration(false); // Tắt loading
      setAutomationComplete(false); // Đánh dấu không hoàn thành
      setErrorRegistration(language === 'en' ?
          `Registration failed: ${err.message || 'Unknown error'}` :
          `Đăng ký thất bại: ${err.message || 'Lỗi không xác định'}`);
      setAutomationMessage(''); // Xóa thông báo tự động hóa nếu có lỗi
    }
  };

  const getMembershipName = (id: string) => {
    // Sẽ lấy tên từ formData.membershipNameFormatted thay vì hardcode
    // Hoặc nếu không có, thì fallback về mapping hiện tại
    const membershipsMap: { [key: string]: string } = {
      "1 day": language === "en" ? "1 Day" : "Gói 1 Ngày", // Đảm bảo khớp với ID từ MembershipScreen
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
          {language === 'en' ? 'Payment Confirmation' : 'Xác nhận Thanh toán'}
        </h2>

        {/* Hiển thị thông tin đã nhập nếu không đang loading và không có lỗi */}
        {!loadingRegistration && !errorRegistration && (
            <div className="bg-white p-6 rounded-lg shadow-md border border-green-200">
              <p className="text-center text-green-700 text-xl font-semibold mb-4">
                {language === 'en' ? 'Payment successful!' : 'Thanh toán thành công!'}
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

        {/* Hiển thị Loader và Message cho toàn bộ quá trình xử lý */}
        {(loadingRegistration || (automationMessage && !automationComplete)) && !errorRegistration && (
            <div className="flex flex-col items-center mt-6">
              <Loader />
              <p className="mt-4 text-lg text-gray-700">{automationMessage}</p>
            </div>
        )}
        {/* Hiển thị thông báo thành công và đếm ngược riêng nếu đã hoàn thành */}
        {automationComplete && !errorRegistration && (
            <div className="flex flex-col items-center mt-6">
              <p className="text-xl font-semibold text-green-700">{automationMessage}</p>
              {formData.customerType === 'returning' && countdownToHome !== null && (
                  <p className="text-lg font-semibold text-blue-600 mt-2">
                    {language === 'en' ? `Returning to Home in ${countdownToHome} seconds...` : `Quay về trang chủ sau ${countdownToHome} giây...`}
                  </p>
              )}
            </div>
        )}

        {/* Hiển thị lỗi nếu có */}
        {errorRegistration && (
            <div className="text-red-600 text-center text-lg">{errorRegistration}</div>
        )}
      </div>
  );
}
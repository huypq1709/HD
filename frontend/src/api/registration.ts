// frontend/src/api/registration.ts
// Đây là file xử lý các cuộc gọi API từ frontend đến backend

interface FormData {
    customerType: string;
    fullName: string;
    phoneNumber: string;
    service: string;
    membership: string;
    [key: string]: any; // Thêm index signature để cho phép các thuộc tính bổ sung
}

export async function registerUser(formData: FormData) { // Sử dụng interface FormData đã định nghĩa
    // Đảm bảo URL này CHÍNH XÁC khớp với cổng và endpoint của Flask backend
    // Backend Flask của bạn đang chạy ở cổng 5007 và endpoint là /api/start-automation
    const API_URL = 'http://localhost:5007/api/start-automation';

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData) // Gửi toàn bộ formData
        });

        if (!response.ok) {
            // Nếu phản hồi không thành công (ví dụ: status 4xx hoặc 5xx)
            // Cố gắng đọc thông báo lỗi từ phản hồi của server
            const errorData = await response.json().catch(() => ({ message: 'Unknown error occurred on server.' }));
            throw new Error(errorData.message || 'Network response was not ok');
        }

        // Nếu thành công, trả về dữ liệu JSON từ backend (chứa status và message)
        return await response.json();
    } catch (error: any) {
        // Xử lý lỗi mạng hoặc lỗi không thể kết nối tới server
        console.error('Error in registerUser (API call):', error);
        // Ném lỗi để ConfirmationScreen có thể bắt và hiển thị cho người dùng
        throw new Error(`Failed to connect to automation server: ${error.message}`);
    }
}
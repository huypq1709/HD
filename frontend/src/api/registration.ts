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

export async function registerUser(formData: FormData) {
    // Sử dụng đường dẫn tương đối để phù hợp với cấu hình Nginx
    const API_URL = '/api/app5/start-automation';

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ 
                message: 'Server error occurred. Please try again later.' 
            }));
            throw new Error(errorData.message || `Server error: ${response.status}`);
        }

        const data = await response.json();
        if (!data) {
            throw new Error('No data received from server');
        }
        return data;
    } catch (error: any) {
        console.error('Error in registerUser (API call):', error);
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            throw new Error('Cannot connect to automation server. Please check if the server is running.');
        }
        throw new Error(`Failed to connect to automation server: ${error.message}`);
    }
}
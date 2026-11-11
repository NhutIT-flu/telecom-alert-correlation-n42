import axios, { AxiosError } from 'axios';

/**
 * Cấu hình Axios Client tập trung cho toàn bộ Frontend Module M7
 * Tách biệt hoàn toàn tầng fetch layer khỏi giao diện người dùng (UI)
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request interceptor (nếu cần gắn traceId, requestTime)
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor chuẩn hóa lỗi
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Chỉ log lỗi trong production; dev dùng mock mode (VITE_USE_MOCK=true) nên không cần log
    if (import.meta.env.PROD) {
      console.error('[API Service Error]:', {
        status: error.response?.status,
        url: error.config?.url,
      });
    }
    return Promise.reject(error);
  }
);

export default apiClient;

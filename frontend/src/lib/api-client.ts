import axios from 'axios'
import { createClient } from './supabase'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const api = {
  // Alert endpoints
  alerts: {
    getCurrent: () => apiClient.get('/api/v1/alerts/current'),
    getHistory: (params?: { 
      start_time?: string
      end_time?: string
      severity?: string
      limit?: number
      offset?: number
    }) => apiClient.get('/api/v1/alerts/history', { params }),
  },
  
  // User endpoints
  users: {
    getProfile: () => apiClient.get('/api/v1/users/profile'),
    updateProfile: (data: Record<string, unknown>) => apiClient.put('/api/v1/users/profile', data),
    getSubscription: () => apiClient.get('/api/v1/users/subscription'),
    updateSubscription: (data: Record<string, unknown>) => apiClient.put('/api/v1/users/subscription', data),
    generateApiKey: () => apiClient.post('/api/v1/users/api-key'),
    getApiUsage: () => apiClient.get('/api/v1/users/usage'),
  },
}

export default apiClient
import axios from 'axios'

// Base URL for the API - automatically detects if running on Vercel or locally
const getBaseURL = () => {
  if (typeof window !== 'undefined') {
    // Browser environment
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8002'
    } else {
      // Production (Vercel) - use relative paths
      return ''
    }
  }
  // Server environment fallback
  return 'http://localhost:8002'
}

const BASE_URL = getBaseURL()

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Transistor API service
export const transistorApi = {
  // Get all transistors
  async getAll() {
    const response = await api.get('/api/transistors')
    return response.data
  },

  // Get a specific transistor by ID
  async getById(id) {
    const response = await api.get(`/api/transistors/${id}`)
    return response.data
  },

  // Create a new transistor
  async create(transistorData) {
    const response = await api.post('/api/transistors', transistorData)
    return response.data
  },

  // Update an existing transistor
  async update(id, transistorData) {
    const response = await api.put(`/api/transistors/${id}`, transistorData)
    return response.data
  },

  // Delete a transistor
  async delete(id) {
    const response = await api.delete(`/api/transistors/${id}`)
    return response.data
  },

  // Validate a transistor
  async validate(id) {
    const response = await api.post(`/api/transistors/${id}/validate`)
    return response.data
  },

  // Compare multiple transistors
  async compare(transistorIds) {
    const response = await api.post('/api/transistors/compare', transistorIds)
    return response.data
  },

  // Export transistor in specified format
  async export(id, format) {
    const response = await api.post(`/api/transistors/${id}/export/${format}`, {}, {
      responseType: 'blob'
    })
    return response.data
  },

  // Upload transistor from file
  async upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/api/transistors/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }
}

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    throw error
  }
)

export default api

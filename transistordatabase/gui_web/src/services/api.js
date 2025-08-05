import axios from 'axios'

// Base URL for the FastAPI backend
const BASE_URL = 'http://localhost:8002/api'

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
    const response = await api.get('/transistors')
    return response.data
  },

  // Get a specific transistor by ID
  async getById(id) {
    const response = await api.get(`/transistors/${id}`)
    return response.data
  },

  // Create a new transistor
  async create(transistorData) {
    const response = await api.post('/transistors', transistorData)
    return response.data
  },

  // Update an existing transistor
  async update(id, transistorData) {
    const response = await api.put(`/transistors/${id}`, transistorData)
    return response.data
  },

  // Delete a transistor
  async delete(id) {
    const response = await api.delete(`/transistors/${id}`)
    return response.data
  },

  // Validate a transistor
  async validate(id) {
    const response = await api.post(`/transistors/${id}/validate`)
    return response.data
  },

  // Compare multiple transistors
  async compare(transistorIds) {
    const response = await api.post('/transistors/compare', transistorIds)
    return response.data
  },

  // Export transistor in specified format
  async export(id, format) {
    const response = await api.post(`/transistors/${id}/export/${format}`, {}, {
      responseType: 'blob'
    })
    return response.data
  },

  // Upload transistor from file
  async upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/transistors/upload', formData, {
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

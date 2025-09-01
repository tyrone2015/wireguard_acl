import { describe, it, expect, vi } from 'vitest'
import axios from 'axios'

// Mock axios before importing request
vi.mock('axios', () => {
  const mockAxiosInstance = {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    create: vi.fn()
  }

  // Make create return the mock instance
  mockAxiosInstance.create.mockReturnValue(mockAxiosInstance)

  return {
    default: mockAxiosInstance
  }
})

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

// Import request after mocking axios
import request from '@/utils/request'

describe('request utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('request instance', () => {
    it('should be an axios instance', () => {
      expect(request).toBeDefined()
      expect(typeof request.get).toBe('function')
      expect(typeof request.post).toBe('function')
      expect(typeof request.put).toBe('function')
      expect(typeof request.delete).toBe('function')
    })

    it('should have interceptors configured', () => {
      expect(request.interceptors).toBeDefined()
      expect(request.interceptors.request).toBeDefined()
      expect(request.interceptors.response).toBeDefined()
    })

    it('should make GET requests', async () => {
      const mockResponse = { data: { success: true } }
      request.get.mockResolvedValue(mockResponse)

      const result = await request.get('/test')

      expect(request.get).toHaveBeenCalledWith('/test')
      expect(result).toEqual(mockResponse)
    })

    it('should make POST requests', async () => {
      const mockResponse = { data: { success: true } }
      const postData = { name: 'test' }
      request.post.mockResolvedValue(mockResponse)

      const result = await request.post('/test', postData)

      expect(request.post).toHaveBeenCalledWith('/test', postData)
      expect(result).toEqual(mockResponse)
    })

    it('should make PUT requests', async () => {
      const mockResponse = { data: { success: true } }
      const putData = { name: 'updated' }
      request.put.mockResolvedValue(mockResponse)

      const result = await request.put('/test', putData)

      expect(request.put).toHaveBeenCalledWith('/test', putData)
      expect(result).toEqual(mockResponse)
    })

    it('should make DELETE requests', async () => {
      const mockResponse = { data: { success: true } }
      request.delete.mockResolvedValue(mockResponse)

      const result = await request.delete('/test')

      expect(request.delete).toHaveBeenCalledWith('/test')
      expect(result).toEqual(mockResponse)
    })

    it('should handle request errors', async () => {
      const mockError = new Error('Network error')
      request.get.mockRejectedValue(mockError)

      await expect(request.get('/test')).rejects.toThrow('Network error')
      expect(request.get).toHaveBeenCalledWith('/test')
    })
  })
})

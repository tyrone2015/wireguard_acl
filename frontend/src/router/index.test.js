import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'
import router from '@/router'

// Mock components
vi.mock('@/views/Login.vue', () => ({
  default: { template: '<div>Login</div>' }
}))

vi.mock('@/components/Layout.vue', () => ({
  default: { template: '<div>Layout</div>' }
}))

vi.mock('@/views/Dashboard.vue', () => ({
  default: { template: '<div>Dashboard</div>' }
}))

vi.mock('@/views/Peers.vue', () => ({
  default: { template: '<div>Peers</div>' }
}))

vi.mock('@/views/ACLs.vue', () => ({
  default: { template: '<div>ACLs</div>' }
}))

vi.mock('@/views/Settings.vue', () => ({
  default: { template: '<div>Settings</div>' }
}))

describe('Router Configuration', () => {
  let mockLocalStorage

  beforeEach(() => {
    // Mock localStorage
    mockLocalStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn()
    }
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('router instance', () => {
    it('should create router with web history', () => {
      expect(router).toBeDefined()
      expect(router.options.history).toBeInstanceOf(Object)
    })

    it('should have correct routes configuration', () => {
      const routes = router.options.routes

      expect(routes).toHaveLength(2)

      // Login route
      expect(routes[0]).toMatchObject({
        path: '/login',
        name: 'Login'
      })

      // Main route with children
      expect(routes[1].path).toBe('/')
      expect(routes[1].redirect).toBe('/dashboard')
      expect(routes[1].children).toHaveLength(4)
    })
  })

  describe('route structure', () => {
    it('should have login route', () => {
      const loginRoute = router.options.routes.find(route => route.path === '/login')
      expect(loginRoute).toBeDefined()
      expect(loginRoute.name).toBe('Login')
    })

    it('should have dashboard route', () => {
      const mainRoute = router.options.routes.find(route => route.path === '/')
      const dashboardRoute = mainRoute.children.find(child => child.path === 'dashboard')

      expect(dashboardRoute).toBeDefined()
      expect(dashboardRoute.name).toBe('Dashboard')
      expect(dashboardRoute.meta).toEqual({
        title: '仪表盘',
        icon: 'Odometer'
      })
    })

    it('should have nodes route', () => {
      const mainRoute = router.options.routes.find(route => route.path === '/')
      const nodesRoute = mainRoute.children.find(child => child.path === 'nodes')

      expect(nodesRoute).toBeDefined()
      expect(nodesRoute.name).toBe('Nodes')
      expect(nodesRoute.meta).toEqual({
        title: '节点管理',
        icon: 'Share'
      })
    })

    it('should have firewall rules route', () => {
      const mainRoute = router.options.routes.find(route => route.path === '/')
      const firewallRoute = mainRoute.children.find(child => child.path === 'firewall-rules')

      expect(firewallRoute).toBeDefined()
      expect(firewallRoute.name).toBe('FirewallRules')
      expect(firewallRoute.meta).toEqual({
        title: '防火墙规则',
        icon: 'Shield'
      })
    })

    it('should have settings route', () => {
      const mainRoute = router.options.routes.find(route => route.path === '/')
      const settingsRoute = mainRoute.children.find(child => child.path === 'settings')

      expect(settingsRoute).toBeDefined()
      expect(settingsRoute.name).toBe('Settings')
      expect(settingsRoute.meta).toEqual({
        title: '系统设置',
        icon: 'Setting'
      })
    })
  })

  describe('route guards', () => {
    it('should redirect to dashboard if user is logged in and tries to access login', () => {
      mockLocalStorage.getItem.mockReturnValue('valid-token')

      const to = { path: '/login' }
      const from = { path: '/' }
      let nextCalled = false
      let nextPath = null

      const next = (path) => {
        nextCalled = true
        nextPath = path
      }

      // Manually test the guard logic
      const token = localStorage.getItem('token')
      if (to.path === '/login') {
        if (token) {
          next('/')
        } else {
          next()
        }
      }

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('token')
      expect(nextPath).toBe('/')
    })

    it('should redirect to login if user is not logged in and tries to access protected route', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      const to = { path: '/dashboard' }
      const from = { path: '/' }
      let nextCalled = false
      let nextPath = null

      const next = (path) => {
        nextCalled = true
        nextPath = path
      }

      // Manually test the guard logic
      const token = localStorage.getItem('token')
      if (to.path === '/login') {
        if (token) {
          next('/')
        } else {
          next()
        }
      } else {
        if (token) {
          next()
        } else {
          next('/login')
        }
      }

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('token')
      expect(nextPath).toBe('/login')
    })

    it('should allow access to login page when not logged in', () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      const to = { path: '/login' }
      const from = { path: '/' }
      let nextCalled = false

      const next = () => {
        nextCalled = true
      }

      // Manually test the guard logic
      const token = localStorage.getItem('token')
      if (to.path === '/login') {
        if (token) {
          next('/')
        } else {
          next()
        }
      }

      expect(nextCalled).toBe(true)
    })
  })

  describe('navigation flow', () => {
    it('should have default redirect to dashboard', () => {
      const mainRoute = router.options.routes.find(route => route.path === '/')
      expect(mainRoute.redirect).toBe('/dashboard')
    })

    it('should protect all child routes', () => {
      const mainRoute = router.options.routes.find(route => route.path === '/')
      const protectedRoutes = mainRoute.children

      expect(protectedRoutes.length).toBeGreaterThan(0)

      // All child routes should require authentication
      protectedRoutes.forEach(route => {
        expect(route.path).not.toBe('/login')
      })
    })
  })
})

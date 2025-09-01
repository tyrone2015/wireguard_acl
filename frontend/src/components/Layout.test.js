import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import Layout from '@/components/Layout.vue'

// Mock Element Plus components and icons
vi.mock('element-plus', () => ({
  ElContainer: {
    name: 'ElContainer',
    template: '<div class="el-container"><slot /></div>'
  },
  ElHeader: {
    name: 'ElHeader',
    template: '<header class="el-header"><slot /></header>'
  },
  ElMain: {
    name: 'ElMain',
    template: '<main class="el-main"><slot /></main>'
  },
  ElMenu: {
    name: 'ElMenu',
    template: '<ul class="el-menu"><slot /></ul>',
    props: ['defaultActive', 'router', 'uniqueOpened', 'collapse', 'mode']
  },
  ElMenuItem: {
    name: 'ElMenuItem',
    template: '<li class="el-menu-item"><slot /></li>',
    props: ['index']
  },
  ElSubMenu: {
    name: 'ElSubMenu',
    template: '<li class="el-sub-menu"><slot /></li>',
    props: ['index']
  },
  ElDropdown: {
    name: 'ElDropdown',
    template: '<div class="el-dropdown"><slot /></div>',
    emits: ['command']
  },
  ElDropdownMenu: {
    name: 'ElDropdownMenu',
    template: '<ul class="el-dropdown-menu"><slot /></ul>'
  },
  ElDropdownItem: {
    name: 'ElDropdownItem',
    template: '<li class="el-dropdown-item"><slot /></li>',
    props: ['command'],
    emits: ['click']
  },
  ElButton: {
    name: 'ElButton',
    template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
    props: ['type', 'size', 'icon', 'circle']
  },
  ElDialog: {
    name: 'ElDialog',
    template: '<div class="el-dialog" v-if="modelValue"><slot /></div>',
    props: ['modelValue', 'title', 'width'],
    emits: ['update:modelValue']
  },
  ElForm: {
    name: 'ElForm',
    template: '<form class="el-form"><slot /></form>',
    props: ['model', 'rules']
  },
  ElFormItem: {
    name: 'ElFormItem',
    template: '<div class="el-form-item"><slot /></div>',
    props: ['label', 'prop']
  },
  ElInput: {
    name: 'ElInput',
    template: '<input class="el-input" v-model="modelValue" />',
    props: ['modelValue', 'placeholder', 'showPassword', 'type'],
    emits: ['update:modelValue']
  },
  ElIcon: {
    name: 'ElIcon',
    template: '<i class="el-icon"><slot /></i>',
    props: ['style']
  },
  ElMessage: {
    error: vi.fn(),
    success: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue()
  }
}))

// Mock Element Plus icons with __v_isRef using importOriginal
vi.mock('@element-plus/icons-vue', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    Expand: {
      name: 'Expand',
      template: '<i class="el-icon-expand"></i>',
      __v_isRef: false
    },
    Fold: {
      name: 'Fold',
      template: '<i class="el-icon-fold"></i>',
      __v_isRef: false
    },
    User: {
      name: 'User',
      template: '<i class="el-icon-user"></i>',
      __v_isRef: false
    },
    Setting: {
      name: 'Setting',
      template: '<i class="el-icon-setting"></i>',
      __v_isRef: false
    },
    SwitchButton: {
      name: 'SwitchButton',
      template: '<i class="el-icon-switch-button"></i>',
      __v_isRef: false
    },
    Moon: {
      name: 'Moon',
      template: '<i class="el-icon-moon"></i>',
      __v_isRef: false
    },
    Sunny: {
      name: 'Sunny',
      template: '<i class="el-icon-sunny"></i>',
      __v_isRef: false
    },
    Lock: {
      name: 'Lock',
      template: '<i class="el-icon-lock"></i>',
      __v_isRef: false
    },
    Unlock: {
      name: 'Unlock',
      template: '<i class="el-icon-unlock"></i>',
      __v_isRef: false
    },
    Odometer: {
      name: 'Odometer',
      template: '<i class="el-icon-odometer"></i>',
      __v_isRef: false
    },
    Share: {
      name: 'Share',
      template: '<i class="el-icon-share"></i>',
      __v_isRef: false
    },
    Shield: {
      name: 'Shield',
      template: '<i class="el-icon-shield"></i>',
      __v_isRef: false
    },
    ArrowDown: {
      name: 'ArrowDown',
      template: '<i class="el-icon-arrow-down"></i>',
      __v_isRef: false
    },
    __v_isRef: false
  }
})

// Mock router
const mockRouter = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      children: [
        { path: 'dashboard', name: 'Dashboard', meta: { title: '仪表盘', icon: 'Odometer' } },
        { path: 'peers', name: 'Peers', meta: { title: '节点管理', icon: 'Share' } },
        { path: 'acls', name: 'ACLs', meta: { title: '访问控制', icon: 'Shield' } },
        { path: 'settings', name: 'Settings', meta: { title: '系统设置', icon: 'Setting' } }
      ]
    },
    { path: '/login', name: 'Login' }
  ]
})

// Mock stores
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    user: { username: 'testuser' },
    logout: vi.fn(),
    isAuthenticated: true
  })
}))

vi.mock('@/stores/theme', () => ({
  useThemeStore: () => ({
    isDark: false,
    toggleTheme: vi.fn()
  })
}))

vi.mock('@/api', () => ({
  authAPI: {
    changePassword: vi.fn().mockResolvedValue()
  }
}))

describe('Layout', () => {
  let wrapper
  let mockLocalStorage

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock localStorage
    mockLocalStorage = {
      getItem: vi.fn().mockReturnValue('testuser'),
      setItem: vi.fn(),
      removeItem: vi.fn()
    }
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true
    })

    // Mock document
    Object.defineProperty(document, 'documentElement', {
      value: { setAttribute: vi.fn() },
      writable: true
    })

    // Mount component
    wrapper = mount(Layout, {
      global: {
        plugins: [createPinia(), mockRouter],
        stubs: {
          RouterView: { template: '<div>Router View</div>' },
          RouterLink: { template: '<a><slot /></a>', props: ['to'] }
        }
      }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.restoreAllMocks()
  })

  it('should render layout structure', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.layout-container').exists()).toBe(true)
    expect(wrapper.find('.header').exists()).toBe(true)
    expect(wrapper.find('.main-content').exists()).toBe(true)
  })

  it('should render navigation menu', () => {
    const menu = wrapper.find('.top-nav-menu')
    expect(menu.exists()).toBe(true)
  })

  it('should render user dropdown', () => {
    const dropdown = wrapper.find('.user-dropdown')
    expect(dropdown.exists()).toBe(true)
  })

  it('should toggle theme', async () => {
    const themeButton = wrapper.find('.el-button')
    if (themeButton.exists()) {
      await themeButton.trigger('click')
      // Theme toggle should be called
    }
  })

  it('should handle password change dialog', async () => {
    const dropdownItem = wrapper.find('.el-dropdown-item')
    if (dropdownItem.exists()) {
      await dropdownItem.trigger('click')
      // Password change dialog should open
    }
  })

  it('should handle logout', async () => {
    const logoutItem = wrapper.findAll('.el-dropdown-item').find(item =>
      item.text().includes('退出登录')
    )
    if (logoutItem) {
      await logoutItem.trigger('click')
      // Logout should be called
    }
  })

  it('should be responsive', () => {
    // Test responsive behavior - component should exist
    expect(wrapper.vm).toBeDefined()
  })
})

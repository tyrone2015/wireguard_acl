import { beforeAll } from 'vitest'

// Mock Element Plus icons
global.matchMedia = global.matchMedia || function() {
  return {
    matches: false,
    addListener: function() {},
    removeListener: function() {}
  }
}

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.sessionStorage = sessionStorageMock

// Mock window.location
delete global.window.location
global.window.location = {
  href: '',
  pathname: '/',
  search: '',
  hash: '',
  reload: vi.fn(),
  assign: vi.fn(),
  replace: vi.fn()
}

// Mock Element Plus components globally
beforeAll(() => {
  // Mock Element Plus components
  const mockComponent = {
    template: '<div><slot /></div>',
    props: ['modelValue', 'loading', 'disabled', 'type', 'size', 'circle', 'icon', 'router', 'defaultActive', 'mode', 'labelWidth', 'rules', 'ref', 'showPassword', 'responseType', 'baseURL', 'timeout', 'headers']
  }

  // Register global mocks for common Element Plus components
  global.ElButton = mockComponent
  global.ElInput = mockComponent
  global.ElForm = mockComponent
  global.ElFormItem = mockComponent
  global.ElDialog = mockComponent
  global.ElTable = mockComponent
  global.ElTableColumn = mockComponent
  global.ElMenu = mockComponent
  global.ElMenuItem = mockComponent
  global.ElDropdown = mockComponent
  global.ElDropdownMenu = mockComponent
  global.ElDropdownItem = mockComponent
  global.ElContainer = mockComponent
  global.ElHeader = mockComponent
  global.ElMain = mockComponent
  global.ElIcon = mockComponent
  global.ElMessage = {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
  global.ElMessageBox = {
    confirm: vi.fn().mockResolvedValue(),
    alert: vi.fn().mockResolvedValue()
  }
})

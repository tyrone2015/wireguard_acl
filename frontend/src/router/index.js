import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Layout from '@/components/Layout.vue'
import Dashboard from '@/views/Dashboard.vue'
import Nodes from '@/views/Peers.vue'
import FirewallRules from '@/views/ACLs.vue'
import Settings from '@/views/Settings.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
  path: 'nodes',
  name: 'Nodes',
  component: Nodes,
        meta: { title: '节点管理', icon: 'Share' }
      },
      {
  path: 'firewall-rules',
  name: 'FirewallRules',
  component: FirewallRules,
        meta: { title: '防火墙规则', icon: 'Shield' }
      },
      {
        path: 'settings',
        name: 'Settings', 
        component: Settings,
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
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
})

export default router

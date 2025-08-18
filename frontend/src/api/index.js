import request from '@/utils/request'

// 认证相关 API
export const authAPI = {
  // 登录
  login(data) {
    return request.post('/login', data, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
  },
  
  // 修改密码
  changePassword(data) {
    return request.post('/change-password', data)
  }
}

// 用户相关 API
export const userAPI = {
  // 获取用户列表
  getUsers() {
    return request.get('/users')
  },
  
  // 创建用户
  createUser(data) {
    return request.post('/users', data)
  },
  
  // 更新用户
  updateUser(id, data) {
    return request.put(`/users/${id}`, data)
  },
  
  // 删除用户
  deleteUser(id) {
    return request.delete(`/users/${id}`)
  }
}

// Peer 相关 API
export const peerAPI = {
  getAvailablePeerIP() {
    return request.get('/peers/available-ip')
  },
  // 获取 Peer 列表
  getPeers() {
    return request.get('/peers')
  },
  // 获取 wg 活跃节点数量（10分钟内有握手的节点数）
  getOnlineNodesCount() {
    return request.get('/wg/online-nodes-count')
  },
  // 创建 Peer
  createPeer(data) {
    return request.post('/peers', data)
  },
  // 更新 Peer
  updatePeer(id, data) {
    return request.put(`/peers/${id}`, data)
  },
  // 删除 Peer
  deletePeer(id) {
    return request.delete(`/peers/${id}`)
  },
  // 生成 Peer 密钥
  generateKey() {
    return request.post('/peers/generate-key')
  },
  // 下载 Peer 配置文件
  downloadPeerConfig(id) {
    // 返回 blob 供前端下载
    return request({
      url: `/peers/${id}/config`,
      method: 'get',
      responseType: 'blob'
    })
  },
  // 获取 Peer 配置二维码
  getPeerConfigQRCode(id) {
    // 返回图片 blob
    return request({
      url: `/peers/${id}/config/qrcode`,
      method: 'get',
      responseType: 'blob'
    })
  },
}

// ACL 相关 API
export const aclAPI = {
  // 获取 ACL 列表
  getACLs() {
    return request.get('/acls')
  },
  // 创建 防火墙
  createACL(data) {
    return request.post('/acls', data)
  },
  // 更新 ACL
  updateACL(id, data) {
    return request.put(`/acls/${id}`, data)
  },
  // 删除 ACL
  deleteACL(id) {
    return request.delete(`/acls/${id}`)
  },
  // 启用 ACL
  enableACL(id) {
    return request.put(`/acls/${id}/enable`)
  },
  // 禁用 ACL
  disableACL(id) {
    return request.put(`/acls/${id}/disable`)
  }
}

// 系统相关 API
export const systemAPI = {
  // 健康检查
  health() {
    return request.get('/health')
  }
}

// 系统资源监控 API
export const systemStatsAPI = {
  stats() {
    return request.get('/system/stats')
  }
}

// 活动日志 API
export const activitiesAPI = {
  getRecent(limit = 4) {
    return request.get(`/activities?limit=${limit}`)
  }
}

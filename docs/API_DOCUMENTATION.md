# WireGuard ACL管理系统 - API文档

## 概述

本文档描述了WireGuard ACL管理系统的REST API接口。

## 认证

所有API请求都需要JWT认证。在请求头中包含：
```
Authorization: Bearer <your_jwt_token>
```

## API端点

### 认证相关

#### POST /login
用户登录
- **请求体**:
```json
{
  "username": "admin",
  "password": "your_password"
}
```
- **响应**:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

#### POST /change-password
修改密码
- **请求体**:
```json
{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

### Peer管理

#### GET /peers
获取所有Peers
- **响应**:
```json
[
  {
    "id": 1,
    "public_key": "public_key_here",
    "allowed_ips": "10.0.0.100/32",
    "remark": "备注",
    "status": true,
    "peer_ip": "10.0.0.100",
    "endpoint": "1.2.3.4:51820",
    "keepalive": 30,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

#### POST /peers
创建新Peer
- **请求体**:
```json
{
  "remark": "新节点",
  "status": true,
  "endpoint": "1.2.3.4:51820",
  "allowed_ips": "10.0.0.100/32",
  "keepalive": 30
}
```

#### PUT /peers/{peer_id}
更新Peer
- **请求体**: 同创建Peer

#### DELETE /peers/{peer_id}
删除Peer

#### POST /peers/batch
批量创建Peers
- **请求体**:
```json
{
  "peers": [
    {
      "remark": "节点1",
      "status": true,
      "endpoint": "1.2.3.4:51820"
    }
  ]
}
```

#### POST /peers/batch-toggle
批量切换Peer状态
- **请求体**:
```json
{
  "peer_ids": [1, 2, 3]
}
```

### ACL管理

#### GET /acls
获取所有ACL规则
- **响应**:
```json
[
  {
    "id": 1,
    "peer_id": 1,
    "action": "allow",
    "target": "192.168.1.0/24",
    "port": "80",
    "protocol": "tcp",
    "enabled": true
  }
]
```

#### POST /acls
创建ACL规则
- **请求体**:
```json
{
  "peer_id": 1,
  "action": "allow",
  "target": "192.168.1.0/24",
  "port": "80",
  "protocol": "tcp"
}
```

#### PUT /acls/{acl_id}
更新ACL规则

#### DELETE /acls/{acl_id}
删除ACL规则

#### POST /acls/batch
批量创建ACL规则

#### POST /acls/batch-toggle
批量切换ACL状态

### 系统监控

#### GET /system/stats
获取系统统计
- **响应**:
```json
{
  "cpu_percent": 45.2,
  "memory": {
    "total": 8589934592,
    "used": 4294967296,
    "percent": 50.0
  },
  "disk": {
    "total": 107374182400,
    "used": 53687091200,
    "percent": 50.0
  },
  "network": {
    "bytes_sent_per_s": 1024,
    "bytes_recv_per_s": 2048
  }
}
```

#### GET /system/advanced-stats
获取高级系统统计

#### GET /system/health-detailed
详细健康检查

### 配置备份

#### GET /backup/export
导出系统配置

#### POST /backup/import
导入系统配置
- **请求体**:
```json
{
  "version": "1.0",
  "peers": [...],
  "acls": [...],
  "server_key": {...}
}
```

#### GET /backup/status
获取备份状态

### 其他

#### GET /health
健康检查

#### GET /activities
获取活动日志

#### GET /wg/online-nodes-count
获取在线节点数量

## 错误响应

所有API在出错时都会返回相应的HTTP状态码和错误信息：

```json
{
  "detail": "错误描述信息"
}
```

常见状态码：
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

## 数据格式说明

### Peer对象
- `id`: 整数，Peer唯一标识
- `public_key`: 字符串，WireGuard公钥
- `private_key`: 字符串，加密存储的私钥
- `allowed_ips`: 字符串，允许的IP地址范围
- `remark`: 字符串，备注信息
- `status`: 布尔值，启用状态
- `peer_ip`: 字符串，分配的IP地址
- `endpoint`: 字符串，对端地址
- `keepalive`: 整数，保持连接间隔(秒)
- `preshared_key`: 字符串，预共享密钥

### ACL对象
- `id`: 整数，规则唯一标识
- `peer_id`: 整数，关联的Peer ID
- `action`: 字符串，"allow" 或 "deny"
- `target`: 字符串，目标IP/CIDR
- `port`: 字符串，端口号或范围
- `protocol`: 字符串，协议类型
- `enabled`: 布尔值，规则启用状态

## 部署指南

### Docker部署

1. 克隆项目：
```bash
git clone <repository_url>
cd wireguard_acl
```

2. 配置环境变量（可选）：
```bash
# 创建.env文件
WG_PEER_IP_CIDR=10.0.0.0/24
WG_SECRET_KEY=your_jwt_secret_key
WG_ADMIN_INIT_PWD=your_admin_password
```

3. 启动服务：
```bash
docker-compose up --build -d
```

4. 访问管理界面：
- 前端: http://localhost:5173
- 后端API: http://localhost:8000

### 手动部署

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 安装WireGuard：
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install wireguard wireguard-tools

# CentOS/RHEL
sudo yum install wireguard-tools
```

3. 配置权限：
```bash
sudo mkdir -p /etc/wireguard
sudo chmod 700 /etc/wireguard
```

4. 启动应用：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 安全配置

1. 修改默认密码：
```bash
# 首次登录后立即修改admin密码
```

2. 配置JWT密钥：
```bash
export WG_SECRET_KEY="your_secure_random_key_here"
```

3. 网络安全：
- 限制API访问IP
- 使用HTTPS
- 配置防火墙规则

### 监控和维护

1. 查看日志：
```bash
docker-compose logs -f backend
```

2. 备份数据：
```bash
# 使用API导出配置
curl -H "Authorization: Bearer <token>" http://localhost:8000/backup/export > backup.json
```

3. 健康检查：
```bash
curl http://localhost:8000/health
curl http://localhost:8000/system/health-detailed
```

## 故障排除

### 常见问题

1. **WireGuard同步失败**
   - 检查WireGuard是否正确安装
   - 确认容器具有NET_ADMIN权限
   - 查看系统日志

2. **数据库连接错误**
   - 检查SQLite文件权限
   - 确认数据目录存在

3. **前端无法访问**
   - 检查端口映射
   - 确认防火墙设置

### 日志位置

- 应用日志：容器内stdout
- WireGuard日志：`/var/log/wireguard/`
- 系统日志：`journalctl -u wg-quick@wg0`

## 版本信息

- API版本: v1.0
- 最后更新: 2024-01-01
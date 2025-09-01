# WireGuard 管理平台 — 功能与用户场景一览 / WireGuard Management Platform — Features & Use Cases

此项目为运维与网络管理员设计的 Web 管理系统，用于集中管理 WireGuard 节点（Peers）及基于 Peer 的访问控制规则（ACL）。目标是通过可视化管理界面简化 Peer 的增删改查、密钥管理、连接状态监控与访问策略配置，从而提升网络管理效率与可视化审计能力。

This project is a web management system designed for operators and network administrators to centrally manage WireGuard peers and peer-based access control rules (ACLs). The goal is to simplify peer CRUD, key management, connection monitoring, and access policy configuration through a visual interface, improving network management efficiency and auditability.

## 开发与维护说明 / Development & Maintenance
当前项目在开发过程中大量使用了 VS Code 的 GitHub Copilot 自动完成功能以提升开发效率。代码中可能包含 Copilot 生成的样板代码或需要人工复审的部分。我会在有时间时逐步审查并修复项目中存在的问题、补充测试覆盖并改进文档与注释。

During development we relied heavily on VS Code's GitHub Copilot to speed up coding. As a result, some code may contain Copilot-generated scaffolding that should be reviewed. We'll gradually audit and fix issues, add test coverage, and improve docs and comments when time permits.

## 核心功能（一句话概览） / Core features (one-line overview)
- 管理 WireGuard 节点（Peer）：创建、编辑、启用/禁用、删除
- 基于 Peer 的防火墙策略（ACL）：按 Peer 精细控制到目标 IP/CIDR、端口与协议的放行或拒绝
- 自动把 Peer 与 ACL 同步为 WireGuard 配置 + iptables 规则
- 生成客户端配置文件并支持二维码展示，方便用户快速导入移动端/桌面客户端
- 简单的用户认证与审计（内置 admin，操作记录可查询）

- Manage WireGuard peers: create, edit, enable/disable, delete
- Peer-based firewall policies (ACLs): fine-grained allow/deny rules by target IP/CIDR, port and protocol
- Automatically sync peers and ACLs into WireGuard config + iptables rules
- Generate client configuration files and QR codes for easy import into mobile/desktop clients
- Basic user authentication and auditing (built-in admin; activity logs available)

## 详细功能点（面向产品使用） / Detailed features (product-facing)

### Peer 管理 / Peer management
- 一键创建 Peer（自动分配 IP、生成密钥对与预共享密钥）
- 支持为每个 Peer 设置备注、Endpoint、Allowed IPs 与 Keepalive
- 可导出单个 Peer 的客户端配置文件（.conf）或二维码，方便远程接入
- 支持启用/禁用 Peer；禁用后不会下发到 WireGuard

 - One-click peer creation (auto IP assignment, key pair and preshared key generation)
 - Support settings per peer: comment, Endpoint, Allowed IPs, PersistentKeepalive
 - Export single-peer client config (.conf) or QR code for easy remote onboarding
 - Enable/disable peers; disabled peers are not pushed to WireGuard

### ACL 管理 / ACL management
- 为指定 Peer 制定放行或拒绝规则（目标 IP/CIDR、端口、协议）
- **新增：支持全局规则** - 创建不绑定特定节点的规则，自动应用于所有活跃的WireGuard节点
- **新增：支持方向控制** - 可选择入口方向、出口方向或双向控制流量
- 支持开启/关闭单条规则，规则改动会被实时同步到内核防火墙（iptables）
- 覆盖式创建：相同 Peer+目标的规则会自动覆盖，避免规则冲突

 - Define allow/deny rules per peer (target IP/CIDR, port, protocol)
 - **New: Global rules support** - Create rules that aren't bound to specific peers, automatically applied to all active WireGuard nodes
 - **New: Direction control** - Choose inbound, outbound, or bidirectional traffic control
 - Rules can be enabled/disabled; changes are synced to the kernel firewall (iptables)
 - Overwrite-on-create: rules with the same peer + target will replace existing ones to avoid conflicts

### 同步与部署 / Sync & Deployment
- 所有 Peer/ACL 的变更会触发一次同步流程：生成 wg 配置并执行重载
- 生成的配置同时包含适配 iptables 的 PostUp/PostDown 命令，便于一键生效/回滚

 - Changes to peers/ACLs trigger a sync process: generate wg config and reload
 - Generated configs include PostUp/PostDown commands that apply iptables rules for one-click apply/rollback

### 运维与可视化 / Operations & Visualization
- 可查看在线 Peer 的统计（基于最近握手时间判断在线）
- 操作会记录为活动日志（Activity），便于审计与排查
- 提供健康检查接口，便于监控集成

 - View peer online statistics (based on last handshake time)
 - Actions are recorded as activity logs for auditing and troubleshooting
 - Health check endpoints available for monitoring integration

## 典型使用场景（谁会用，解决什么问题） / Typical use cases
- 远程办公场景：为每位员工快速下发 WireGuard 配置与二维码，按需限制每台终端能访问的目标服务与端口
- IOT/边缘设备管理：对接入的设备按 ID（Peer）精确控制它们对内网敏感段或外部服务的访问
- 多租户/团队隔离：为不同团队的 Peer 分别下发 ACL，保证网络层面的最小权限原则
- 快速应急隔离：当某台设备异常时，一键禁用 Peer 或下发 deny 规则，立即阻断风险流量

- Remote work: quickly issue WireGuard configs and QR codes per employee, restrict each device to allowed services/ports
- IoT/edge device management: control access by device ID (peer) to sensitive internal segments or external services
- Multi-tenant/team isolation: apply separate ACLs per team to enforce least privilege at the network layer
- Rapid incident isolation: disable a peer or push deny rules to immediately block risky traffic

## 快速上手（面向运维） / Quick start (for operators)
- 推荐以 Docker Compose 启动（项目内已包含 docker-compose 配置），常见步骤：

```bash
# 在项目根目录 / from project root
docker-compose up --build -d
```

- 管理界面访问：启动后访问前端服务（默认在 5173 端口，或由部署时的端口映射决定），使用初始 admin 帐号登录（初始密码：admin123）。
- 常见操作流程：
 1. 登录管理界面 -> 进入 Peers -> 新建 Peer（记录备注与分配 IP）
 2. 进入 ACL -> 为刚建的 Peer 添加 Allow 或 Deny 规则（填写目标 IP/CIDR 与端口）
 3. **可选：创建全局规则** - 在ACL页面选择"全局规则（所有节点）"，创建适用于所有节点的统一策略
 4. **可选：设置方向控制** - 选择"入口方向"、"出口方向"或"双向"来精确控制流量方向
 5. 下载 Peer 的配置或二维码，用户导入客户端即可连通

 - Access the UI: after start, open the frontend (default port 5173 or as mapped). Login with the initial admin account (default password: admin123).
 - Typical flow:
   1. Log in -> Peers -> Create a peer (add comment and assign IP)
   2. ACL -> Add Allow or Deny rules for that peer (target IP/CIDR and ports)
   3. **Optional: Create global rules** - In ACL page select "Global Rule (All Nodes)" to create unified policies for all nodes
   4. **Optional: Set direction control** - Choose "inbound", "outbound", or "both" for precise traffic direction control
   5. Download peer config or QR; user imports into client to connect

## 安全与注意事项（简短） / Security & notes
- 请修改默认 admin 密码并设置强密码。生产环境务必设置 JWT 签名密钥（环境变量）。
- 项目会在主机上执行 WireGuard 与 iptables 命令，部署时请确保宿主允许并具备相应能力（容器通常需 NET_ADMIN 权限）。
- 私钥会在数据库中加密保存，但建议做好数据库与备份的访问控制。

- Change the default admin password and use a strong password. In production set a JWT signing key via environment variables.
- The project executes WireGuard and iptables commands on the host. Ensure the host permits these operations (containers typically need NET_ADMIN capability).
- Private keys are stored encrypted in the database, but control access to the DB and backups.

## 部署与使用建议 / Deployment & operational suggestions
- 在生产环境上线前，先在测试环境完成策略验证与连接测试，确保无误后按变更管理流程逐步发布。
- 定期备份配置与规则库，并开启审计日志以便事后分析。

- Before going to production, validate policies and connectivity in a test environment and follow change management for rollout.
- Regularly back up configs and rule store, and enable audit logs for post-incident analysis.

## 详细使用指南 / Detailed usage guides

### ACL方向控制使用指南
请参考 [`ACL_DIRECTION_GUIDE.md`](ACL_DIRECTION_GUIDE.md) 获取关于ACL方向控制的详细使用说明，包括：
- 入口方向、出口方向和双向规则的区别
- 实际应用场景和配置示例
- 前端界面操作步骤
- 故障排除和最佳实践

### 全局ACL规则使用指南
请参考 [`GLOBAL_ACL_GUIDE.md`](GLOBAL_ACL_GUIDE.md) 获取关于全局ACL规则的详细使用说明，包括：
- 全局规则的特性和适用范围
- 创建和管理全局规则的方法
- 与节点特定规则的优先级关系
- 安全策略和最佳实践

### API文档
请参考 [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md) 获取完整的API接口文档。


# 项目文件组织说明

## 目录结构概述

WireGuard ACL 管理平台采用了清晰的文件组织结构，便于开发、维护和部署。

## 详细目录说明

### 📁 app/ - 后端应用
```
app/
├── __init__.py          # 应用初始化
├── main.py             # FastAPI应用入口
├── models.py           # SQLAlchemy数据模型
├── acl.py              # ACL相关API接口
├── peer.py             # Peer管理API接口
├── auth.py             # 用户认证
├── sync.py             # 配置同步和iptables管理
├── config.py           # 应用配置
├── db.py               # 数据库连接和会话管理
├── key_manager.py      # WireGuard密钥管理
├── settings.py         # 应用设置
├── activity.py         # 操作日志记录
├── backup.py           # 数据备份功能
└── system_status.py    # 系统状态监控
```

### 📁 frontend/ - 前端应用
```
frontend/
├── src/
│   ├── main.js         # Vue应用入口
│   ├── App.vue         # 根组件
│   ├── components/     # Vue组件
│   ├── views/          # 页面视图
│   ├── router/         # 路由配置
│   ├── stores/         # Pinia状态管理
│   ├── api/            # API调用封装
│   └── utils/          # 工具函数
├── public/             # 静态资源
├── package.json        # Node.js依赖配置
├── vite.config.js      # Vite构建配置
├── vitest.config.js    # Vitest测试配置
└── Dockerfile.frontend  # 前端Docker镜像配置
```

### 📁 docs/ - 项目文档
```
docs/
├── README.md                    # 项目主要说明文档
├── API_DOCUMENTATION.md         # 完整的API接口文档
├── guides/                      # 使用指南
│   ├── ACL_DIRECTION_GUIDE.md   # ACL方向控制使用指南
│   ├── GLOBAL_ACL_GUIDE.md      # 全局ACL规则使用指南
│   └── IMPLEMENTATION_SUMMARY.md # 功能实现总结
└── implementation/              # 实现文档
    ├── ACL_DIRECTION_IMPLEMENTATION.md    # 方向控制实现详情
    └── GLOBAL_ACL_IMPLEMENTATION.md       # 全局规则实现详情
```

### 📁 scripts/ - 脚本工具
```
scripts/
├── demo/                        # 演示脚本
│   ├── demo_acl_direction.py    # ACL方向控制演示
│   └── demo_global_acl.py       # 全局ACL规则演示
├── test/                        # 测试和验证脚本
│   ├── test_acl_direction.py    # 方向控制功能测试
│   ├── test_global_acl.py       # 全局规则功能测试
│   ├── validate_acl_direction.py # 方向控制验证
│   └── validate_improvements.py  # 改进验证
├── migration/                   # 数据库迁移脚本
│   ├── migrate_acl_direction.py # 添加方向字段迁移
│   └── migrate_acl_nullable.py  # 字段可空性迁移
└── final_validation.py          # 最终功能验证脚本
```

### 📁 config/ - 配置文件
```
config/
├── docker-compose.yml     # Docker Compose编排配置
├── Dockerfile.backend     # 后端Docker镜像构建文件
└── requirements.txt       # Python依赖包列表
```

### 📁 bin/ - 可执行脚本
```
bin/
├── run_backend.sh         # 后端服务启动脚本
└── run_dev.sh             # 开发环境启动脚本
```

### 📁 tests/ - 单元测试
```
tests/
├── conftest.py            # pytest配置和fixtures
├── test_api.py            # API接口测试
├── test_crypto.py         # 加密功能测试
└── test_utils.py          # 工具函数测试
```

### 📁 data/ - 数据目录
```
data/
└── wireguard_acl.db       # SQLite数据库文件
```

## 文件分类原则

### 1. 按功能分类
- **核心功能**：app/ 目录包含所有后端业务逻辑
- **用户界面**：frontend/ 目录包含所有前端代码
- **数据存储**：data/ 目录包含数据库和持久化数据
- **测试代码**：tests/ 目录包含所有测试文件

### 2. 按用途分类
- **文档**：docs/ 目录包含所有文档文件
- **脚本**：scripts/ 目录包含各种工具脚本
- **配置**：config/ 目录包含配置文件
- **可执行**：bin/ 目录包含可执行脚本

### 3. 按开发阶段分类
- **演示脚本**：scripts/demo/ 用于功能演示
- **测试脚本**：scripts/test/ 用于功能验证
- **迁移脚本**：scripts/migration/ 用于数据库迁移

## 优势

### 1. 清晰的职责分离
- 每个目录都有明确的职责范围
- 文件位置与功能高度相关
- 易于理解和维护

### 2. 便于开发协作
- 开发者可以快速定位相关文件
- 减少文件冲突的可能性
- 支持并行开发

### 3. 易于部署和维护
- 配置文件集中管理
- 脚本工具分类存放
- 文档结构化组织

### 4. 支持扩展
- 新功能可以按相同模式组织
- 目录结构具有良好的扩展性
- 便于添加新的分类目录

## 使用建议

### 开发时
1. 在相应目录下创建新文件
2. 遵循现有的命名约定
3. 更新相关文档

### 部署时
1. 使用 `config/docker-compose.yml` 进行容器化部署
2. 使用 `bin/` 目录下的脚本启动服务
3. 参考 `docs/` 目录下的文档进行配置

### 维护时
1. 定期运行 `scripts/test/` 下的验证脚本
2. 使用 `scripts/migration/` 进行数据库迁移
3. 更新 `docs/` 下的相关文档

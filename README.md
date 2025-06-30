# 智训v3 - 智能对话训练系统

## 项目概述

智训v3是一个基于AI的智能对话训练系统，旨在帮助用户在各种业务场景下进行对话训练。系统支持多种AI API接入方式，包括Dify API和WhaleDI API，提供灵活的配置选项以适应不同的训练场景。

### 技术栈

- **后端**: Python + Flask + SQLite
- **前端**: HTML5 + CSS3 + JavaScript
- **AI集成**: Dify API + WhaleDI API
- **部署**: Docker + Docker Compose

## 项目结构

```
智训v3/
├── app.py                          # 主应用文件，包含所有后端逻辑
├── requirements.txt                # Python依赖包
├── Dockerfile                      # Docker镜像配置
├── docker-compose.yml             # Docker Compose配置
├── agent_config.db                # SQLite数据库文件
├── init_db.py                     # 数据库初始化脚本
├── migrate_db.py                  # 数据库迁移脚本
├── insert_default_config.py       # 默认配置插入脚本
├── init_api_config.py             # API配置初始化脚本
├── cs.html                        # 主前端界面
├── templates/                     # HTML模板目录
│   ├── admin.html                # 管理员后台界面
│   ├── login.html                # 登录页面
│   ├── test-agent.html           # 训练端界面
│   ├── index.html                # 首页
│   ├── content.html              # 内容页面
│   ├── outline.html              # 大纲页面
│   ├── topic.html                # 主题页面
│   └── content_generator.html    # 内容生成页面
├── static/                        # 静态资源目录
│   ├── css/                      # 样式文件
│   ├── js/                       # JavaScript文件
│   └── fonts/                    # 字体文件
└── instance/                      # 实例目录（运行时生成）
```

## 系统架构与数据流转

### 1. 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面层     │    │   后端服务层     │    │   数据存储层     │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │  登录页面   │ │    │ │  Flask App  │ │    │ │ SQLite DB   │ │
│ │ login.html  │ │    │ │   app.py    │ │    │ │agent_config │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │    .db      │ │
│                 │    │                 │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │
│ │ 训练端界面  │ │◄───┤ │  对话API    │ │    │ ┌─────────────┐ │
│ │test-agent   │ │    │ │ 接口处理    │ │    │ │ 用户表      │ │
│ │   .html     │ │    │ └─────────────┘ │    │ │ User        │ │
│ └─────────────┘ │    │                 │    │ └─────────────┘ │
│                 │    │ ┌─────────────┐ │    │                 │
│ ┌─────────────┐ │    │ │  管理API    │ │    │ ┌─────────────┐ │
│ │ 管理端界面  │ │◄───┤ │ 接口处理    │ │    │ │ 配置表      │ │
│ │ admin.html  │ │    │ └─────────────┘ │    │ │ Config      │ │
│ └─────────────┘ │    │                 │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    │                 │
                                              │ ┌─────────────┐ │
                                              │ │ 对话历史表  │ │
                                              │ │Conversation│ │
                                              │ │  History    │ │
                                              │ └─────────────┘ │
                                              └─────────────────┘
```

### 2. 用户认证流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   用户注册   │───►│   用户登录   │───►│   Token生成  │───►│  权限验证   │
│             │    │             │    │             │    │             │
│ POST /api/  │    │ POST /api/  │    │ JWT Token   │    │ @require_   │
│ register    │    │ login       │    │ 存储到前端   │    │ token       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 管理员激活  │    │ 密码验证     │    │ 请求头携带  │    │ 路由访问    │
│ 用户状态    │    │ 用户状态检查 │    │ Authorization│    │ 功能使用    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 3. 对话训练流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  选择配置   │───►│  开始会话   │───►│  发送消息   │───►│  AI响应     │
│             │    │             │    │             │    │             │
│ 业务场景    │    │ POST /api/  │    │ POST /api/  │    │ Dify API    │
│ 角色设定    │    │ start-      │    │ conversa-   │    │ WhaleDI API │
│ 话术配置    │    │ session     │    │ tion        │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 前端界面    │    │ 会话ID生成  │    │ 消息存储    │    │ 响应处理    │
│ 配置选择    │    │ 数据库记录  │    │ 历史记录    │    │ 前端展示    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 结束会话    │    │ 会话状态    │    │ 对话统计    │    │ 历史查看    │
│ POST /api/  │    │ 更新为结束  │    │ 数据统计    │    │ 日志导出    │
│ end-session │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 4. 管理后台流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  管理员登录 │───►│  后台界面   │───►│  功能管理   │───►│  数据操作   │
│             │    │             │    │             │    │             │
│ 权限验证    │    │ admin.html  │    │ 用户管理    │    │ 数据库CRUD │
│ is_admin    │    │ 多Tab界面   │    │ 配置管理    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 用户管理    │    │ 配置管理    │    │ 对话统计    │    │ 系统监控    │
│ 激活/禁用   │    │ 增删改查    │    │ 用户统计    │    │ API状态     │
│ 角色设置    │    │ 业务参数    │    │ 对话日志    │    │ 系统状态    │
│ 密码重置    │    │ API配置     │    │ 数据导出    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 核心功能模块

### 1. 用户认证模块
- **用户注册**: `/api/register` - 新用户注册
- **用户登录**: `/api/login` - 用户登录认证
- **权限验证**: `@require_token` 装饰器 - 接口权限控制
- **管理员权限**: `@require_token(admin_only=True)` - 管理员专用接口

### 2. 对话训练模块
- **会话管理**: 
  - `POST /api/start-session` - 开始新会话
  - `POST /api/conversation` - 继续对话
  - `POST /api/end-session` - 结束会话
- **AI集成**:
  - Dify API - 智能对话服务
  - WhaleDI API - 知识服务API
- **配置支持**: 业务场景、角色设定、话术配置

### 3. 配置管理模块
- **业务配置**: 联系方式、业务场景、模拟角色、训练角色、营销方法、示例话术
- **API配置**: Dify和WhaleDI的URL和密钥配置
- **接口支持**: 
  - `GET /api/config` - 获取配置选项
  - `GET /api/api-config` - 获取API配置

### 4. 管理后台模块
- **用户管理**: 
  - 用户列表查看
  - 用户激活/禁用
  - 角色设置（管理员/普通用户）
  - 密码重置
- **配置管理**: 各配置项的增删改查
- **数据统计**: 
  - 对话统计
  - 用户对话统计
  - 对话日志查看
  - 数据导出功能

## 数据库设计

### 核心数据表

| 表名 | 说明 | 主要字段 |
|-----|------|---------|
| `User` | 用户表 | id, username, password_hash, userid, is_active, is_admin |
| `ConversationHistory` | 对话历史 | id, config, messages, status, timestamp, end_time, api_type |
| `ApiConfig` | API配置 | id, name, url, key, type |
| `Lianxifangshi` | 联系方式 | id, name |
| `Yewuchangjing` | 业务场景 | id, name |
| `Monijuese` | 模拟角色 | id, name |
| `Xunlianjuese` | 训练角色 | id, name |
| `Yingxiaodafa` | 营销方法 | id, name |
| `Shilihuashu` | 示例话术 | id, name |

## API接口文档

### 认证接口
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录

### 对话接口
- `POST /api/start-session` - 开始会话
- `POST /api/conversation` - 继续对话
- `POST /api/end-session` - 结束会话

### 配置接口
- `GET /api/config` - 获取配置选项
- `GET /api/api-config` - 获取API配置

### 管理接口
- `GET /api/admin/<type>` - 获取配置项
- `POST /api/admin/<type>` - 添加配置项
- `DELETE /api/admin/<type>/<id>` - 删除配置项
- `GET /api/users` - 获取用户列表
- `POST /api/users/<id>/activate` - 激活用户
- `POST /api/users/<id>/deactivate` - 禁用用户
- `POST /api/users/<id>/reset-password` - 重置密码
- `POST /api/users/<id>/set-role` - 设置角色
- `GET /api/admin/conversation-stats` - 对话统计
- `GET /api/admin/user-conversation-stats` - 用户对话统计
- `GET /api/admin/conversation-logs` - 对话日志
- `GET /api/admin/conversation-logs/export` - 导出对话日志

## 部署指南

### 环境要求
- Python 3.7+
- Flask框架
- SQLite3数据库
- 现代浏览器（支持HTML5和CSS3）

### 快速部署

#### 1. 传统部署
```bash
# 克隆项目
git clone <项目地址>
cd 智训v3

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动服务
python app.py
```

#### 2. Docker部署
```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 配置说明

#### API配置
```python
# Dify API
DIFY_API_URL = "http://8.148.26.204:41/v1/chat-messages"
DIFY_API_KEY = "app-UC0l1p6JW9r5cFG3TZIJi6t0"

# WhaleDI API
WHALEDI_API_URL = "http://10.10.186.14:31001/knowledge/knowledgeService/api/v1/chat/completions"
WHALEDI_API_KEY = "WhaleDI-Agent-7fc20b57f24c62fe70153616382dfbf87d38baf52dcd632fd50d4f48b871af61"
```

#### 数据库配置
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///agent_config.db'
```

## 使用说明

### 1. 系统初始化
1. 启动系统后，访问登录页面
2. 注册第一个用户（默认为普通用户）
3. 管理员登录后台，激活新用户或设置管理员权限
4. 配置API密钥和业务参数

### 2. 对话训练
1. 用户登录系统
2. 选择训练场景和角色设定
3. 选择API类型（Dify或WhaleDI）
4. 开始对话训练
5. 查看AI反馈和训练效果

### 3. 管理后台
1. 管理员登录后台
2. 用户管理：激活用户、设置角色、重置密码
3. 配置管理：管理业务参数和API配置
4. 数据统计：查看对话统计和日志

## 系统特性

### 安全性
- JWT Token认证
- 密码加密存储
- 权限分级控制
- CORS跨域支持
- 参数白名单验证

### 可靠性
- API调用失败自动重试
- 会话状态维护
- 必填参数校验
- 错误恢复机制
- 多API故障转移

### 用户体验
- 现代化UI设计
- 响应式布局
- 实时对话展示
- 毛玻璃效果
- 动画过渡效果

## 维护与支持

### 日常维护
- 定期检查数据库状态
- 监控API调用成功率
- 更新配置选项
- 备份重要数据

### 故障排除
- 检查API连接状态
- 验证数据库完整性
- 查看系统日志
- 测试API切换功能

## 注意事项

1. 确保API密钥的有效性和安全性
2. 定期备份数据库文件
3. 监控系统资源使用情况
4. 及时更新配置信息
5. 测试不同API的可用性
6. 注意用户权限管理

## 未来展望

1. 支持更多AI API接入
2. 增加数据分析功能
3. 优化用户界面体验
4. 添加更多训练模式
5. 支持多语言国际化
6. 增加API性能监控
7. 支持云端部署和扩展

---

**智训v3** - 让AI对话训练更简单、更高效！ 
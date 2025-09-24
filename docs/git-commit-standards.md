# Git Commit消息规范

## 1. 消息格式规范

### 1.1 基本格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 1.2 格式说明
- **type**: 必填，修改类型
- **scope**: 可选，影响范围
- **subject**: 必填，简短描述
- **body**: 可选，详细描述
- **footer**: 可选，补充信息

## 2. Type类型规范

### 2.1 主要类型
| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(auth): add user login functionality` |
| `fix` | 修复bug | `fix(api): resolve memory leak in request handler` |
| `docs` | 文档更新 | `docs(readme): update installation instructions` |
| `style` | 代码格式调整 | `style(format): apply ruff formatting to src/app` |
| `refactor` | 重构代码 | `refactor(utils): simplify data processing logic` |
| `test` | 测试相关 | `test(api): add unit tests for user endpoints` |
| `chore` | 构建或工具变动 | `chore(deps): update ruff to latest version` |

### 2.2 特殊类型
| 类型 | 说明 | 使用场景 |
|------|------|----------|
| `perf` | 性能优化 | 数据库查询优化、缓存策略 |
| `ci` | CI配置修改 | GitHub Actions、GitLab CI |
| `build` | 构建系统修改 | Dockerfile、Makefile |
| `revert` | 代码回滚 | 回滚之前的提交 |

## 3. Scope范围规范

### 3.1 常用Scope
```
app          # 应用核心功能
auth         # 认证授权
api          # API接口
db           # 数据库
ui           # 用户界面
utils        # 工具函数
config       # 配置管理
tests        # 测试代码
docs         # 文档
deps         # 依赖管理
ci           # CI/CD
deploy       # 部署相关
```

### 3.2 Scope使用示例
```bash
feat(auth): add OAuth2 integration
fix(api): resolve 500 error in user endpoint
style(app): format code with ruff
test(utils): add unit tests for validation functions
```

## 4. Subject标题规范

### 4.1 标题要求
- 使用现在时态，不是过去时
- 首字母小写，不以句号结尾
- 不超过50个字符
- 清晰表达修改内容

### 4.2 正确示例
```bash
feat(auth): add user registration feature
fix(api): handle empty request body properly
docs(readme): update quick start guide
```

### 4.3 错误示例
```bash
# 错误：使用过去时
feat(auth): added user registration

# 错误：首字母大写
Feat(auth): Add user registration

# 错误：以句号结尾
feat(auth): add user registration feature.
```

## 5. Body正文规范

### 5.1 正文要求
- 详细描述修改内容和原因
- 说明修改的影响范围
- 列出相关的技术决策
- 提供测试方法

### 5.2 正文格式
```bash
feat(auth): add JWT token authentication

Implement JWT-based authentication system with the following features:
- Token generation and validation
- Refresh token mechanism
- Password hashing with bcrypt
- Rate limiting for auth endpoints

Technical decisions:
- Use PyJWT for token handling
- Store refresh tokens in Redis
- Implement token rotation strategy

Testing:
- Added unit tests for token generation
- Integration tests for auth flow
- Load tests for token validation
```

## 6. Footer页脚规范

### 6.1 Breaking Changes
```bash
feat(api): change user response format

BREAKING CHANGE: User response format has changed from:
{
  "username": "john",
  "email": "john@example.com"
}
to:
{
  "user": {
    "username": "john",
    "email": "john@example.com"
  }
}
```

### 6.2 关联Issue
```bash
fix(auth): resolve login timeout issue

Closes #123
Related to #124
```

### 6.3 代码审查
```bash
Reviewed-by: @team-lead
Approved-by: @tech-lead
```

## 7. 提交示例

### 7.1 功能提交
```bash
feat(auth): add two-factor authentication

Implement TOTP-based two-factor authentication for enhanced security.
Users can now enable 2FA in their profile settings and use
authenticator apps for login.

Features implemented:
- QR code generation for setup
- TOTP token validation
- Backup codes generation
- Recovery process for lost devices

Security considerations:
- Tokens expire after 30 seconds
- Rate limiting prevents brute force attacks
- Backup codes are one-time use only

Testing:
- Unit tests for TOTP generation/validation
- Integration tests with existing auth flow
- End-to-end tests for 2FA setup process

Closes #456
BREAKING CHANGE: Auth response now includes 2FA status
```

### 7.2 修复提交
```bash
fix(api): handle database connection timeouts

Add connection pooling and retry logic to prevent database
connection timeouts during high traffic periods.

Changes made:
- Implemented connection pooling with SQLAlchemy
- Added exponential backoff for retries
- Added circuit breaker pattern
- Improved error logging and monitoring

Impact:
- Reduced connection errors by 95%
- Improved API response times
- Better handling of database outages

Testing:
- Load testing with simulated database failures
- Integration tests with real database
- Monitoring of error rates in production

Closes #789
```

### 7.3 文档提交
```bash
docs(api): update API documentation

Update OpenAPI specification with latest endpoint changes
and add examples for all authentication methods.

Changes:
- Added new user endpoints
- Updated response schemas
- Added authentication examples
- Improved error documentation

Reviewed-by: @tech-writer
```

## 8. 提交检查规则

### 8.1 强制检查
- ✅ 符合格式规范
- ✅ type在允许范围内
- ✅ subject长度不超过50字符
- ✅ 不使用特殊字符
- ✅ 关联issue或任务号

### 8.2 建议检查
- ✅ 提供详细body
- ✅ 包含测试信息
- ✅ 说明影响范围
- ✅ 代码审查签名

## 9. 常见错误避免

### 9.1 格式错误
```bash
# 错误：缺少type
add user login feature

# 错误：type不正确
bugfix: resolve login issue

# 错误：subject太长
feat(auth): implement comprehensive user authentication system with multiple providers including OAuth2 and JWT tokens
```

### 9.2 内容错误
```bash
# 错误：描述不清
fix: fixed some bugs

# 错误：缺少技术细节
feat: added new feature

# 错误：没有关联issue
fix: resolved critical bug
```

## 10. 工具支持

### 10.1 提交验证工具
- commitlint: 提交消息格式验证
- conventional-changelog: 自动生成changelog
- git hooks: 强制执行规范

### 10.2 VSCode集成
- Conventional Commits插件
- GitLens插件
- Commit message templates

---

**重要**: 所有提交必须遵循此规范，确保代码历史清晰可追踪。

# Git 工作流指南

## 概述

本文档为开发者提供完整的 Git 工作流程指南，确保团队协作的一致性和代码质量。

## 快速开始

### 1. 安装和配置

```bash
# 克隆仓库
git clone <repository-url>
cd gunicorn_uvicorn_fastapi_sse

# 安装 Git hooks
python scripts/install-git-hooks.py

# 配置用户信息（如果尚未配置）
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. 日常开发流程

```bash
# 1. 从最新的 develop 分支创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# 2. 开发并提交更改
# ... 进行代码更改 ...
git add .
git commit -m "feat: add new feature description"

# 3. 推送到远程仓库
git push origin feature/your-feature-name

# 4. 创建 Pull Request
# 在 GitHub 上创建从 feature/your-feature-name 到 develop 的 PR

# 5. 代码审查和合并
# 等待 CI/CD 检查通过
# 等待团队成员审查
# 合并到 develop 分支
```

## 分支管理

### 分支类型

| 类型 | 前缀 | 目标分支 | 生命周期 | 说明 |
|------|------|----------|----------|------|
| 功能分支 | `feature/` | `develop` | 临时 | 开发新功能 |
| 修复分支 | `hotfix/` | `main` | 临时 | 紧急问题修复 |
| 发布分支 | `release/` | `main` | 临时 | 版本发布准备 |
| 实验分支 | `experiment/` | - | 临时 | 实验性功能 |

### 分支命名规范

```bash
# 功能分支
feature/user-authentication
feature/payment-integration
feature/api-performance-optimization

# 修复分支
hotfix/login-bug-fix
hotfix/security-patch
hotfix/production-issue

# 发布分支
release/v1.0.0
release/v2.1.3

# 实验分支
experiment/ai-model-integration
experiment/new-ui-framework
```

### 分支生命周期

1. **创建分支**：从对应的基础分支创建
2. **开发**：在分支上进行开发，频繁提交
3. **测试**：确保所有测试通过
4. **审查**：创建 Pull Request 进行代码审查
5. **合并**：合并到目标分支后删除源分支

## Commit 规范

### Commit 格式

```
<type>[<scope>]: <description>

[body]

[footer]
```

### Commit 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: add user login` |
| `fix` | 问题修复 | `fix: resolve memory leak` |
| `docs` | 文档更新 | `docs: update API documentation` |
| `style` | 代码格式化 | `style: format code with ruff` |
| `refactor` | 重构 | `refactor: simplify user service` |
| `test` | 测试相关 | `test: add unit tests for auth` |
| `ci` | CI/CD 配置 | `ci: update GitHub Actions` |
| `build` | 构建相关 | `build: upgrade dependencies` |
| `perf` | 性能优化 | `perf: improve database queries` |
| `security` | 安全相关 | `security: add input validation` |

### Commit 示例

```bash
# 功能提交
feat(auth): add user registration endpoint
- Add email validation
- Implement password hashing
- Add unit tests

# 修复提交
fix(api): handle SSE connection timeouts
- Add retry logic for failed connections
- Increase timeout duration
- Log connection errors

# 文档提交
docs: update deployment guide
- Add Docker deployment instructions
- Update environment variables section
- Fix broken links
```

## Git Hooks 验证

### 自动验证规则

1. **分支名称验证**
   - 必须符合命名规范
   - 不能使用保留名称
   - 必须有适当的前缀

2. **Commit 消息验证**
   - 必须遵循 conventional commit 格式
   - 标题行不能超过 72 字符
   - 必须包含有效的类型和范围

3. **代码质量验证**
   - 代码格式化检查
   - 类型检查
   - 测试覆盖率

### 处理验证失败

```bash
# 如果 commit 被拒绝
git commit -m "invalid commit message"  # 会被拒绝

# 查看错误信息
# 根据提示修改 commit 消息

# 重新提交
git commit -m "feat: add valid commit message"
```

## Pull Request 流程

### 创建 PR

1. **选择正确的目标分支**
   - 功能分支 → `develop`
   - 修复分支 → `main`
   - 发布分支 → `main`

2. **填写 PR 描述**
   ```markdown
   ## 变更描述
   简要描述这个 PR 的目的和变更内容。

   ## 变更类型
   - [ ] 新功能
   - [ ] 问题修复
   - [ ] 文档更新
   - [ ] 重构
   - [ ] 性能优化

   ## 测试清单
   - [ ] 单元测试通过
   - [ ] 集成测试通过
   - [ ] 手动测试完成

   ## 相关问题
   Closes #123
   ```

### PR 审查清单

- [ ] 代码符合项目规范
- [ ] 测试覆盖率充分
- [ ] 文档已更新
- [ ] 性能影响已考虑
- [ ] 安全问题已检查
- [ ] 向后兼容性已验证

## 问题排查

### 常见问题

1. **分支名称被拒绝**
   ```bash
   # 检查分支名称
   git branch -m feature/invalid-name feature/correct-name
   ```

2. **Commit 消息格式错误**
   ```bash
   # 修改最近的 commit 消息
   git commit --amend -m "feat: correct commit message"
   ```

3. **CI/CD 检查失败**
   ```bash
   # 查看检查失败原因
   # 在 GitHub Actions 中查看详细日志
   # 修复问题后推送新的 commit
   ```

### 获取帮助

```bash
# 查看分支规范
cat docs/git-branch-standards.md

# 查看 commit 规范
cat docs/git-commit-standards.md

# 运行手动验证
python scripts/validate-branch-name.py your-branch-name
```

## 最佳实践

### 日常开发

1. **频繁提交**：小步快跑，每个功能点单独提交
2. **清晰描述**：commit 消息要清晰描述变更内容
3. **及时同步**：定期从基础分支同步最新代码
4. **保持整洁**：删除已合并的分支，保持仓库整洁

### 团队协作

1. **代码审查**：每个 PR 都需要至少一人审查
2. **持续集成**：确保所有检查通过后再合并
3. **文档同步**：代码变更同步更新相关文档
4. **问题追踪**：使用 issues 追踪问题和功能需求

### 版本发布

1. **发布分支**：从 `develop` 创建 `release` 分支
2. **版本号**：遵循语义化版本控制
3. **发布说明**：为每个版本编写发布说明
4. **标签管理**：为每个发布版本创建 Git 标签

## 工具和脚本

### 自动化脚本

```bash
# 安装 Git hooks
python scripts/install-git-hooks.py

# 生成分支报告
python scripts/branch-report.py

# 清理过期分支
python scripts/branch-cleanup.py

# 验证分支名称
python scripts/validate-branch-name.py feature/your-feature
```

### 快捷命令

```bash
# 查看当前分支状态
git status

# 查看最近的提交
git log --oneline -10

# 查看分支列表
git branch -a

# 删除已合并的本地分支
git branch --merged | grep -v 'main\|develop' | xargs git branch -d
```

---

**注意**：遵循这些规范将确保代码库的一致性和可维护性。如有疑问，请咨询团队负责人或查看相关文档。

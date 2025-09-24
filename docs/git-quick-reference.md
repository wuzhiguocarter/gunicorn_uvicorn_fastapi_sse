# Git 工作流快速参考

## 分支操作

### 创建分支
```bash
# 功能分支
git checkout develop
git pull origin develop
git checkout -b feature/feature-name

# 修复分支
git checkout main
git pull origin main
git checkout -b hotfix/issue-name

# 发布分支
git checkout develop
git pull origin develop
git checkout -b release/version
```

### 分支管理
```bash
# 查看分支
git branch -a

# 切换分支
git checkout branch-name

# 删除本地分支
git branch -d branch-name

# 删除远程分支
git push origin --delete branch-name

# 清理已合并的本地分支
git branch --merged | grep -v 'main\|develop' | xargs git branch -d
```

## Commit 操作

### 基本提交
```bash
# 添加所有更改
git add .

# 提交更改
git commit -m "feat: add new feature"

# 推送到远程
git push origin branch-name
```

### Commit 修改
```bash
# 修改最近的 commit 消息
git commit --amend -m "feat: improved commit message"

# 修改多个 commit
git rebase -i HEAD~n

# 撤销最近的 commit
git reset --soft HEAD~1
```

## Pull Request 流程

### 创建 PR
```bash
# 1. 推送功能分支
git push origin feature/feature-name

# 2. 在 GitHub 上创建 PR
# 目标分支：develop（功能）或 main（修复）
```

### PR 合并后
```bash
# 切换到 develop
git checkout develop
git pull origin develop

# 删除本地功能分支
git branch -d feature/feature-name
```

## Commit 消息格式

### 标准格式
```
<type>[<scope>]: <description>

[body]

[footer]
```

### 常用类型
- `feat`: 新功能
- `fix`: 问题修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 重构
- `test`: 测试相关
- `ci`: CI/CD 配置
- `build`: 构建相关
- `perf`: 性能优化
- `security`: 安全相关

### 示例
```bash
git commit -m "feat(auth): add user login"
git commit -m "fix(api): resolve connection timeout"
git commit -m "docs: update deployment guide"
git commit -m "style: format code with ruff"
```

## 分支命名规范

### 功能分支
```bash
feature/user-authentication
feature/payment-integration
feature/api-optimization
```

### 修复分支
```bash
hotfix/login-bug
hotfix/security-patch
hotfix/production-issue
```

### 发布分支
```bash
release/v1.0.0
release/v2.1.3
```

### 实验分支
```bash
experiment/ai-integration
experiment/new-framework
```

## 常用命令

### 状态查看
```bash
git status
git log --oneline -10
git diff
git diff --staged
```

### 同步操作
```bash
git pull origin branch-name
git fetch origin
git push origin branch-name
```

### 冲突解决
```bash
git merge origin/branch-name
# 解决冲突后
git add .
git commit -m "fix: resolve merge conflicts"
```

### 撤销操作
```bash
# 撤销工作区更改
git checkout -- file-name

# 撤销暂存区更改
git reset HEAD file-name

# 撤销 commit
git reset --soft HEAD~1
```

## 验证命令

### 分支验证
```bash
python scripts/validate-branch-name.py feature/your-feature
```

### 代码质量检查
```bash
make check-all
make lint
make format
make type-check
```

### 测试
```bash
make test
make test-coverage
```

## Git Hooks

### 安装 Hooks
```bash
python scripts/install-git-hooks.py
```

### Hook 类型
- `pre-commit`: 代码质量检查
- `commit-msg`: 消息格式验证
- `pre-push`: 推送前检查
- `prepare-commit-msg`: 消息模板

## 紧急情况处理

### 跳过验证（紧急情况）
```bash
git commit --no-verify -m "紧急修复"
git push --no-verify
```

### 强制推送（谨慎使用）
```bash
git push --force-with-lease origin branch-name
```

### 恢复丢失的 commit
```bash
git reflog
git reset --hard HEAD@{n}
```

## CI/CD 故障排除

### 本地测试
```bash
# 运行与 CI 相同的检查
make check-all

# 查看测试结果
make test-coverage
```

### 修复问题
```bash
# 修复代码格式
make format

# 修复类型错误
make type-check

# 修复测试失败
make test
```

## 分支管理工具

### 生成分支报告
```bash
python scripts/branch-report.py
```

### 清理过期分支
```bash
# 预览
python scripts/branch-cleanup.py --dry-run

# 执行清理
python scripts/branch-cleanup.py
```

## 快速参考卡片

### 日常开发流程
```bash
# 1. 创建功能分支
git checkout develop && git pull origin develop && git checkout -b feature/name

# 2. 开发和提交
git add . && git commit -m "feat: description"

# 3. 推送和创建 PR
git push origin feature/name

# 4. 合并后清理
git checkout develop && git pull origin develop && git branch -d feature/name
```

### 紧急修复流程
```bash
# 1. 创建修复分支
git checkout main && git pull origin main && git checkout -b hotfix/issue

# 2. 修复和提交
git add . && git commit -m "fix: resolve issue"

# 3. 推送和创建 PR
git push origin hotfix/issue

# 4. 合并后清理
git checkout main && git pull origin main && git branch -d hotfix/issue
```

---

**提示**：将此文档保存为书签，便于快速查阅常用命令和流程。

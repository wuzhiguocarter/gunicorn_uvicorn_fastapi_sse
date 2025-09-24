# Git 工作流问题排查

## 常见问题和解决方案

### 分支相关问题

#### 1. 分支名称验证失败

**错误信息**：
```
❌ 分支名称 'feature/invalid-name' 不符合规范
```

**解决方案**：
```bash
# 重命名分支为符合规范的名称
git branch -m feature/invalid-name feature/user-authentication

# 或者使用正确的命名格式
git branch -m old-name feature/new-feature-name
```

#### 2. 分支推送被拒绝

**错误信息**：
```
! [rejected] feature/my-feature -> feature/my-feature (non-fast-forward)
```

**解决方案**：
```bash
# 同步远程分支的最新更改
git fetch origin feature/my-feature
git rebase origin/feature/my-feature

# 如果有冲突，解决冲突后继续
git add .
git rebase --continue

# 推送更新
git push origin feature/my-feature
```

#### 3. 分支删除失败

**错误信息**：
```
error: The branch 'feature/my-feature' is not fully merged.
```

**解决方案**：
```bash
# 强制删除未合并的分支（谨慎使用）
git branch -D feature/my-feature

# 删除远程分支
git push origin --delete feature/my-feature
```

### Commit 相关问题

#### 1. Commit 消息格式错误

**错误信息**：
```
❌ Commit 消息不符合规范
```

**解决方案**：
```bash
# 修改最近的 commit 消息
git commit --amend -m "feat: add user authentication"

# 如果是多个 commit，使用 interactive rebase
git rebase -i HEAD~n
```

#### 2. Hook 验证失败

**错误信息**：
```
husky - pre-commit hook exited with code 1 (error)
```

**解决方案**：
```bash
# 跳过 hook（不推荐，仅用于紧急情况）
git commit --no-verify -m "your commit message"

# 或者修复问题后重新提交
# 修复代码格式或测试问题
git add .
git commit -m "fix: resolve formatting issues"
```

#### 3. Commit 修改后需要推送到远程

```bash
# 修改 commit 消息后需要强制推送
git commit --amend -m "feat: improved commit message"
git push --force-with-lease origin feature/my-feature
```

### CI/CD 相关问题

#### 1. GitHub Actions 检查失败

**错误信息**：
```
❌ Validate Branch Name - failed
❌ Validate Commit Messages - failed
```

**解决方案**：

**分支名称问题**：
```bash
# 检查分支命名规范
python scripts/validate-branch-name.py your-branch-name

# 重命名分支
git branch -m invalid-name feature/correct-name
git push --force-with-lease origin feature/correct-name
```

**Commit 消息问题**：
```bash
# 查看 commit 历史
git log --oneline

# 使用 interactive rebase 修改 commit 消息
git rebase -i HEAD~n

# 重新推送
git push --force-with-lease origin your-branch
```

#### 2. 代码质量检查失败

**错误信息**：
```
❌ Code Quality Checks - failed
❌ Run Tests - failed
```

**解决方案**：
```bash
# 本地运行相同的检查
make check-all
make test

# 或者单独运行
make lint
make format
make type-check

# 修复问题后提交
git add .
git commit -m "style: fix code formatting issues"
```

### 远程仓库问题

#### 1. 权限问题

**错误信息**：
```
ERROR: Permission to repository denied
```

**解决方案**：
```bash
# 检查远程仓库配置
git remote -v

# 重新配置远程仓库
git remote set-url origin https://github.com/username/repository.git

# 检查 SSH 密钥
ssh -T git@github.com
```

#### 2. 网络连接问题

**错误信息**：
```
Failed to connect to github.com port 443
```

**解决方案**：
```bash
# 检查网络连接
ping github.com

# 使用代理（如果需要）
git config --global http.proxy http://proxy-server:port

# 或者使用 SSH
git remote set-url origin git@github.com:username/repository.git
```

### 分支保护问题

#### 1. 直接推送到受保护分支

**错误信息**：
```
GH006: Protected branch update failed for refs/heads/main
```

**解决方案**：
```bash
# 创建功能分支
git checkout -b feature/hotfix main

# 进行修改并提交
git add .
git commit -m "fix: resolve critical issue"

# 推送到远程
git push origin feature/hotfix

# 在 GitHub 上创建 PR
```

#### 2. PR 合并冲突

**解决方案**：
```bash
# 更新本地分支
git fetch origin main
git rebase origin/main

# 解决冲突
# 编辑冲突文件
git add conflicted-file.py
git rebase --continue

# 推送更新
git push origin feature/my-feature
```

### Git Hooks 问题

#### 1. Hook 不工作

**症状**：提交时没有进行验证

**解决方案**：
```bash
# 重新安装 hooks
python scripts/install-git-hooks.py

# 检查 hook 权限
chmod +x .git/hooks/*

# 手动测试 hook
./.git/hooks/pre-commit
```

#### 2. Hook 脚本错误

**错误信息**：
```
.git/hooks/pre-commit: line 1: python: command not found
```

**解决方案**：
```bash
# 检查 Python 路径
which python3

# 更新 hook 脚本的 shebang
# 编辑 .git/hooks/pre-commit
# 将 #!/usr/bin/env python 改为 #!/usr/bin/env python3

# 或者重新安装 hooks
python scripts/install-git-hooks.py
```

### 性能问题

#### 1. Git 操作缓慢

**解决方案**：
```bash
# 清理 Git 垃圾
git gc --prune=now

# 检查仓库大小
git count-objects -vH

# 使用浅克隆（如果历史记录不重要）
git clone --depth 1 <repository-url>
```

#### 2. 分支过多导致管理困难

**解决方案**：
```bash
# 生成分支报告
python scripts/branch-report.py

# 清理已合并的分支
python scripts/branch-cleanup.py --dry-run

# 确认后执行清理
python scripts/branch-cleanup.py
```

### 集成开发环境问题

#### 1. VS Code Git 集成问题

**解决方案**：
```bash
# 检查 VS Code Git 配置
code --list-extensions | grep git

# 重新安装 Git 扩展
code --install-extension ms-vscode.git

# 清理 VS Code 缓存
rm -rf ~/.vscode/extensions/ms-vscode.git-*
```

#### 2. IDE 中的 Git 操作失败

**解决方案**：
```bash
# 使用命令行进行 Git 操作
git status
git add .
git commit -m "feat: add feature"

# 检查 Git 配置
git config --list
```

## 调试工具和命令

### 1. 调试命令

```bash
# 查看 Git 配置
git config --list

# 查看远程仓库信息
git remote -v

# 查看分支信息
git branch -av

# 查看 commit 历史
git log --oneline --graph --all

# 查看 Git 状态
git status
```

### 2. 验证工具

```bash
# 验证分支名称
python scripts/validate-branch-name.py your-branch

# 验证 commit 消息
echo "feat: test commit" | python scripts/validate-commit-message.py

# 检查代码质量
make check-all
```

### 3. 系统诊断

```bash
# 检查 Python 环境
python --version
which python

# 检查 Git 版本
git --version

# 检查网络连接
curl -I https://github.com
```

## 联系支持

如果以上解决方案无法解决您的问题，请联系团队负责人或提交 issue。

### 提交问题信息

```markdown
## 问题描述
简要描述您遇到的问题。

## 错误信息
```
错误信息粘贴在这里
```

## 复现步骤
1. 执行的操作
2. 预期结果
3. 实际结果

## 环境信息
- 操作系统：[操作系统版本]
- Git 版本：[Git 版本]
- Python 版本：[Python 版本]
- 项目分支：[分支名称]
```

---

**提示**：大多数 Git 问题都可以通过仔细阅读错误信息和遵循解决方案来解决。如果您不确定某个操作，请在测试环境中先尝试。

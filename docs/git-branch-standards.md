# Git分支管理规范

## 1. 分支策略

### 1.1 主分支
- **main**: 主分支，始终保持可部署状态
  - 只允许通过Pull Request合并
  - 必须通过所有CI检查
  - 分支保护：禁止直接推送

### 1.2 开发分支
- **develop**: 开发分支，集成最新功能
  - 从main分支创建
  - 功能分支合并到develop
  - 定期合并到main

### 1.3 功能分支
- **feature/***: 新功能开发
  - 命名格式: `feature/功能名称-任务号`
  - 示例: `feature/user-authentication-123`
  - 从develop分支创建
  - 完成后合并回develop

### 1.4 修复分支
- **hotfix/***: 紧急修复
  - 命名格式: `hotfix/问题描述-任务号`
  - 示例: `hotfix/memory-leak-456`
  - 从main分支创建
  - 同时合并到main和develop

### 1.5 发布分支
- **release/***: 发布准备
  - 命名格式: `release/v版本号`
  - 示例: `release/v1.0.0`
  - 从develop分支创建
  - 测试完成后合并到main和develop

### 1.6 实验分支
- **experiment/***: 实验性功能
  - 命名格式: `experiment/技术方案-开发者`
  - 示例: `experiment/new-arch-john`
  - 用于探索性开发

## 2. 分支生命周期

```
main (生产环境)
│
├── develop (开发集成)
│   ├── feature/user-auth-123 (功能开发)
│   ├── feature/api-optimization-124 (功能开发)
│   └── experiment/new-cache-system (实验性)
│
├── release/v1.0.0 (发布准备)
│
└── hotfix/security-patch-456 (紧急修复)
```

## 3. 分支操作规范

### 3.1 创建功能分支
```bash
# 切换到develop分支
git checkout develop
git pull origin develop

# 创建功能分支
git checkout -b feature/your-feature-name-ticket-number
```

### 3.2 创建修复分支
```bash
# 从main创建紧急修复分支
git checkout main
git pull origin main
git checkout -b hotfix/issue-description-ticket-number
```

### 3.3 分支合并流程
1. 功能分支 → develop
2. develop → main (发布时)
3. hotfix → main + develop

## 4. 分支保护规则

### 4.1 main分支保护
- ❌ 禁止强制推送
- ❌ 禁止直接推送
- ✅ 要求Pull Request
- ✅ 要求状态检查通过
- ✅ 要求代码审查

### 4.2 develop分支保护
- ❌ 禁止强制推送
- ✅ 要求Pull Request
- ✅ 要求状态检查通过

## 5. 分支清理策略

### 5.1 自动清理
- 合并后的功能分支在7天后自动删除
- 实验分支在30天后自动删除

### 5.2 手动清理
```bash
# 查看已合并分支
git branch --merged

# 删除已合并分支
git branch -d branch-name

# 强制删除未合并分支（谨慎使用）
git branch -D branch-name
```

## 6. 分支命名规范

### 6.1 功能分支
- 格式: `feature/功能简述-任务号`
- 长度: 不超过50字符
- 使用小写字母和连字符
- 示例: `feature/add-user-login-123`

### 6.2 修复分支
- 格式: `hotfix/问题描述-任务号`
- 长度: 不超过50字符
- 使用小写字母和连字符
- 示例: `hotfix/fix-memory-leak-456`

### 6.3 发布分支
- 格式: `release/v版本号`
- 版本号遵循语义化版本
- 示例: `release/v1.0.0`

## 7. 违规处理

### 7.1 分支命名违规
- CI自动拦截并提示修正
- 记录违规次数
- 超过3次需团队leader审批

### 7.2 分支保护违规
- 立即回滚违规操作
- 团队内部通报
- 重复违规者权限降级

## 8. 工具支持

### 8.1 分支创建脚本
- 提供`git-create-branch`命令
- 自动验证分支命名
- 自动设置分支追踪

### 8.2 分支清理工具
- 定期清理僵尸分支
- 发送清理通知
- 提供分支统计报告

---

**注意**: 所有分支操作必须遵循此规范，确保代码质量和团队协作效率。

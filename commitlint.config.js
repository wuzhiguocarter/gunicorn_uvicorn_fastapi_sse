module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新功能
        'fix',      // 修复bug
        'docs',     // 文档更新
        'style',    // 代码格式调整
        'refactor', // 重构代码
        'test',     // 测试相关
        'chore',    // 构建或工具变动
        'perf',     // 性能优化
        'ci',       // CI配置修改
        'build',    // 构建系统修改
        'revert',   // 代码回滚
      ],
    ],
    'type-case': [2, 'always', 'lower-case'],
    'type-empty': [2, 'never'],
    'scope-case': [2, 'always', 'lower-case'],
    'subject-case': [2, 'never', ['sentence-case', 'start-case', 'pascal-case', 'upper-case']],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 72],
    'body-leading-blank': [1, 'always'],
    'body-max-line-length': [2, 'always', 100],
    'footer-leading-blank': [1, 'always'],
    'footer-max-line-length': [2, 'always', 100],
  },
  prompt: {
    questions: {
      type: {
        description: '选择你要提交的更改类型:',
        enum: {
          feat: {
            description: '新功能',
            title: 'Features',
            emoji: '✨',
          },
          fix: {
            description: '修复bug',
            title: 'Bug Fixes',
            emoji: '🐛',
          },
          docs: {
            description: '文档更新',
            title: 'Documentation',
            emoji: '📚',
          },
          style: {
            description: '代码格式调整',
            title: 'Styles',
            emoji: '💎',
          },
          refactor: {
            description: '重构代码',
            title: 'Code Refactoring',
            emoji: '📦',
          },
          test: {
            description: '测试相关',
            title: 'Tests',
            emoji: '🚨',
          },
          chore: {
            description: '构建或工具变动',
            title: 'Chores',
            emoji: '🔧',
          },
          perf: {
            description: '性能优化',
            title: 'Performance Improvements',
            emoji: '🚀',
          },
          ci: {
            description: 'CI配置修改',
            title: 'Continuous Integrations',
            emoji: '⚙️',
          },
          build: {
            description: '构建系统修改',
            title: 'Builds',
            emoji: '📦',
          },
          revert: {
            description: '代码回滚',
            title: 'Reverts',
            emoji: '🗑️',
          },
        },
      },
      scope: {
        description: '此更改的范围是什么（例如组件或文件名）:',
      },
      subject: {
        description: '写一个简短的变更描述:',
      },
      body: {
        description: '提供更详细的变更描述:',
      },
      isBreaking: {
        description: '是否有破坏性更改?',
      },
      breakingBody: {
        description: '破坏性更改的详细描述:',
      },
      breaking: {
        description: '描述破坏性更改:',
      },
      isIssueAffected: {
        description: '此变更是否影响任何开放的issue?',
      },
      issuesBody: {
        description: '如果issues被关闭，提交需要一个body。请输入更长的变更描述:',
      },
      issues: {
        description: '添加issue引用 (例如 "fix #123", "re #123".):',
      },
    },
  },
};

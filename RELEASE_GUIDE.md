# MAgentClaw 发布指南

## 版本信息

**当前版本**: v1.3.0  
**发布日期**: 2026 年 3 月 8 日  
**状态**: Stable  

## 发布清单

### 1. 发布前检查

- [ ] 所有测试通过（`pytest test_*.py -v`）
- [ ] 代码质量检查通过（`flake8 maagentclaw`）
- [ ] 类型检查通过（`mypy maagentclaw`）
- [ ] 文档已更新
- [ ] CHANGELOG.md 已更新
- [ ] 版本号已更新（setup.py, pyproject.toml）

### 2. 构建包

```bash
# 安装构建工具
pip install build wheel twine

# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 构建包
python -m build
python -m wheel

# 检查构建的文件
ls -lah dist/
# 应该看到：
# - maagentclaw-1.3.0.tar.gz
# - maagentclaw-1.3.0-py3-none-any.whl
```

### 3. 测试包

```bash
# 在虚拟环境中测试
python -m venv test-env
source test-env/bin/activate  # Windows: test-env\Scripts\activate

# 安装本地包
pip install dist/maagentclaw-1.3.0-py3-none-any.whl

# 测试导入
python -c "import maagentclaw; print(maagentclaw.__version__)"

# 运行基本功能
python -c "from maagentclaw.managers.skill_manager import SkillManager; print('OK')"
```

### 4. 上传到 TestPyPI

```bash
# 上传到测试 PyPI
twine upload --repository testpypi dist/*

# 验证上传
pip install -i https://test.pypi.org/simple/ maagentclaw==1.3.0
```

### 5. 上传到 PyPI

```bash
# 上传到正式 PyPI
twine upload dist/*

# 验证上传
pip install maagentclaw==1.3.0
```

### 6. 创建 GitHub Release

```bash
# 打标签
git tag -a v1.3.0 -m "Release v1.3.0"
git push origin v1.3.0

# GitHub Actions 会自动创建 Release
# 或者手动在 GitHub 上创建 Release
```

## 发布后验证

### 1. 测试安装

```bash
# 在新环境中测试
python -m venv verify-env
source verify-env/bin/activate  # Windows: verify-env\Scripts\activate

# 从 PyPI 安装
pip install maagentclaw==1.3.0

# 验证版本
python -c "import maagentclaw; print(maagentclaw.__version__)"

# 运行测试
python -c "from maagentclaw.managers import SkillManager, ToolManager, HeartbeatManager; print('All managers imported successfully')"
```

### 2. 文档验证

- [ ] README.md 中的安装说明正确
- [ ] 快速开始指南有效
- [ ] API 文档最新

### 3. 功能验证

```bash
# 测试心跳
python -c "from maagentclaw.managers.heartbeat_manager import HeartbeatManager; print('✓ Heartbeat OK')"

# 测试技能
python -c "from maagentclaw.managers.skill_manager import SkillManager; print('✓ Skills OK')"

# 测试工具
python -c "from maagentclaw.managers.tool_manager import ToolManager; print('✓ Tools OK')"
```

## 通知

### 1. 更新通知

- [ ] GitHub Release Notes
- [ ] 项目文档网站
- [ ] 社区论坛

### 2. 社交媒体

- [ ] Twitter/X
- [ ] LinkedIn
- [ ] 技术社区

## 回滚流程

如果发布后发现问题，需要回滚：

```bash
# 1. 从 PyPI 删除包（需要管理员权限）
twine upload --skip-existing dist/*  # 这会跳过已存在的版本

# 2. 删除 Git 标签
git tag -d v1.3.0
git push origin --delete v1.3.0

# 3. 删除 GitHub Release
# 在 GitHub 上手动删除 Release

# 4. 修复问题后重新发布
# 更新版本号为 v1.3.1
# 重复上述发布流程
```

## 自动化发布

项目配置了 GitHub Actions 自动发布：

### 1. 测试工作流

触发条件：push 到 main/develop 分支或 PR

```yaml
.github/workflows/test.yml
```

### 2. PyPI 发布工作流

触发条件：创建 Release

```yaml
.github/workflows/pypi.yml
```

### 3. Release 创建工作流

触发条件：创建标签（v*）

```yaml
.github/workflows/release.yml
```

## 密钥配置

需要在 GitHub 配置以下密钥：

- `PYPI_API_TOKEN` - PyPI API 令牌
- `TEST_PYPI_API_TOKEN` - TestPyPI API 令牌
- `GITHUB_TOKEN` - 自动配置

### 获取 PyPI API 令牌

1. 访问 https://pypi.org/manage/account/token/
2. 创建新的 API 令牌
3. 复制令牌并添加到 GitHub Secrets

### 获取 TestPyPI API 令牌

1. 访问 https://test.pypi.org/manage/account/token/
2. 创建新的 API 令牌
3. 复制令牌并添加到 GitHub Secrets

## 版本命名

遵循语义化版本控制（Semantic Versioning）：

- **MAJOR.MINOR.PATCH** (e.g., 1.3.0)
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能
- **PATCH**: 向后兼容的 bug 修复

### 版本更新规则

```
1.2.0 -> 1.3.0  (新功能)
1.3.0 -> 1.3.1  (bug 修复)
1.3.0 -> 2.0.0  (破坏性变更)
```

## 发布频率

- **Major 版本**: 每 3-6 个月
- **Minor 版本**: 每 2-4 周
- **Patch 版本**: 根据需要

## 发布检查清单模板

```markdown
## Release Checklist

### Pre-release
- [ ] All tests pass
- [ ] Code quality checks pass
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version numbers updated

### Build
- [ ] Package builds successfully
- [ ] Package tested locally
- [ ] Upload to TestPyPI
- [ ] TestPyPI installation verified

### Release
- [ ] Upload to PyPI
- [ ] PyPI installation verified
- [ ] GitHub Release created
- [ ] Git tag pushed

### Post-release
- [ ] Documentation site updated
- [ ] Community notified
- [ ] Social media posts
```

## 故障排查

### 问题：构建失败

```bash
# 清理构建缓存
rm -rf dist/ build/ *.egg-info
pip install --upgrade build wheel
python -m build
```

### 问题：上传失败

```bash
# 检查凭证
twine register -r pypi
twine register -r testpypi

# 重新上传
twine upload dist/*
```

### 问题：安装失败

```bash
# 清除 pip 缓存
pip cache purge

# 重新安装
pip install --no-cache-dir maagentclaw==1.3.0
```

## 参考资源

- [Python 打包指南](https://packaging.python.org/)
- [PyPI 文档](https://pypi.org/help/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [语义化版本](https://semver.org/)

---

**最后更新**: 2026 年 3 月 8 日  
**维护者**: MAgentClaw Team

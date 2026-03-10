# 🦞 MAgentClaw - 快速启动指南

## 一、环境要求

- Python 3.8+
- Windows PowerShell / Linux Bash / macOS Terminal

## 二、快速启动（3 步）

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2: 运行测试（可选）

```bash
python test_maagentclaw.py
```

### 步骤 3: 启动系统

```bash
python maagentclaw/main.py
```

## 三、访问界面

启动后打开浏览器访问：

```
http://localhost:8000
```

## 四、Windows 用户快捷方式

双击运行 `start.ps1` 脚本（需要 PowerShell）

或者在命令行执行：

```powershell
.\start.ps1
```

## 五、验证安装

如果看到以下输出，说明系统运行正常：

```
MAgentClaw 系统初始化完成
Web 界面地址：http://localhost:8000
按 Ctrl+C 退出
```

## 六、基本操作

1. **查看 Agent**: 在主页可以看到所有 Agent
2. **启动 Agent**: 点击"启动"按钮
3. **发送消息**: 点击"发消息"按钮，输入消息后发送
4. **停止 Agent**: 点击"停止"按钮

## 七、常见问题

### Q: 依赖安装失败？
A: 确保 pip 是最新版本：`pip install --upgrade pip`

### Q: 端口被占用？
A: 修改 maagentclaw/main.py 中的端口号（默认 8000）

### Q: 看不到界面？
A: 确保防火墙允许 8000 端口访问

### Q: Agent 没有响应？
A: 确保先点击"启动"按钮激活 Agent

## 八、下一步

- 📖 阅读 [README.md](README.md) 了解项目详情
- 📚 查看 [USAGE.md](USAGE.md) 学习使用方法
- 🔧 参考 [DEVELOPMENT.md](DEVELOPMENT.md) 进行扩展开发
- 📊 查看 [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 了解完整功能

## 九、停止服务

按 `Ctrl+C` 停止服务

---

**祝你使用愉快！** 🎉

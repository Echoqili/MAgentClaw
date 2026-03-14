# MAgentClaw 多角色 Agent 快速配置指南

## 快速开始

```bash
pip install maagentclaw
python maagentclaw/main.py
```

## 配置多角色 Agent

在 `config/agents.json` 中配置：

```json
{
  "ceo": {"name": "CEO", "role": "executive", "temperature": 0.7},
  "cfo": {"name": "CFO", "role": "finance", "temperature": 0.5},
  "cto": {"name": "CTO", "role": "technology", "temperature": 0.7}
}
```

详见 [docs/guides/](docs/guides/)

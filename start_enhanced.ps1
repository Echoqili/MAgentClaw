# MAgentClaw 增强版启动脚本 (Conda 环境)
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "MAgentClaw 增强版启动" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 设置项目路径
$PROJECT_ROOT = "D:\pyworkplace\MAgentClaw"

# 设置 PYTHONPATH
$env:PYTHONPATH = $PROJECT_ROOT
Write-Host "✓ PYTHONPATH: $PROJECT_ROOT" -ForegroundColor Green
Write-Host ""

# 启动程序
Write-Host "正在启动 MAgentClaw 增强版..." -ForegroundColor Yellow
Write-Host ""
python maagentclaw/main_enhanced.py

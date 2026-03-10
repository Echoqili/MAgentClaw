# 快速启动脚本

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "MAgentClaw 快速启动" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python 环境：$pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未找到 Python 环境，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host ""
Write-Host "检查依赖..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt -q
    Write-Host "✓ 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "❌ 未找到 requirements.txt" -ForegroundColor Red
    exit 1
}

# 创建配置目录
Write-Host ""
Write-Host "创建配置目录..." -ForegroundColor Yellow
if (-not (Test-Path "maagentclaw\config")) {
    New-Item -ItemType Directory -Force -Path "maagentclaw\config" | Out-Null
}
if (-not (Test-Path "maagentclaw\logs")) {
    New-Item -ItemType Directory -Force -Path "maagentclaw\logs" | Out-Null
}
if (-not (Test-Path "maagentclaw\workspaces")) {
    New-Item -ItemType Directory -Force -Path "maagentclaw\workspaces" | Out-Null
}
Write-Host "✓ 目录创建完成" -ForegroundColor Green

# 运行测试
Write-Host ""
Write-Host "运行系统测试..." -ForegroundColor Yellow
python test_maagentclaw.py

# 启动主程序
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "启动 MAgentClaw 系统..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Web 管理界面：http://localhost:8000" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

python maagentclaw\main.py

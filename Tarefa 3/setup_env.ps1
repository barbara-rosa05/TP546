# setup_env.ps1
# Script para criar a venv, ativar e instalar dependências do SafeSleep

$ErrorActionPreference = "Stop"

Write-Host ">> Indo para a pasta do projeto..."
Set-Location $PSScriptRoot

# 1) Criar venv se ainda não existir
if (-not (Test-Path ".venv")) {
    Write-Host ">> Criando ambiente virtual .venv ..."
    py -m venv .venv
} else {
    Write-Host ">> Ambiente virtual .venv já existe, pulando criação."
}

# 2) Ativar a venv
Write-Host ">> Ativando .venv ..."
& ".\.venv\Scripts\Activate.ps1"

# 3) Atualizar pip e instalar dependências
Write-Host ">> Atualizando pip ..."
python -m pip install --upgrade pip

Write-Host ">> Instalando dependências do requirements.txt ..."
pip install -r requirements.txt

Write-Host ""
Write-Host "==============================================="
Write-Host " Ambiente pronto! Comandos para usar depois:"
Write-Host "  (com a venv já ativada)"
Write-Host ""
Write-Host "  # Terminal 1 - Logger"
Write-Host "  python services\logger.py"
Write-Host ""
Write-Host "  # Terminal 2 - Simulador SafeSleep"
Write-Host "  python src\safesleep_simulator.py"
Write-Host "==============================================="
Write-Host ""

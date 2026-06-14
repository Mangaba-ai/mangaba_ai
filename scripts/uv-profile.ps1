# Script para simplificar uso de UV no PowerShell
# Adicione isto ao seu perfil PowerShell para usar 'uv' diretamente

# Função para usar UV
function uv {
    & ".\.venv\Scripts\uv.exe" @args
}

# Aliases para comandos comuns
Set-Alias -Name uvs -Value { & ".\.venv\Scripts\uv.exe" sync }
Set-Alias -Name uvrun -Value { & ".\.venv\Scripts\uv.exe" run python }
Set-Alias -Name uvpip -Value { & ".\.venv\Scripts\uv.exe" pip }

Write-Host "✅ Funções UV carregadas!" -ForegroundColor Green
Write-Host "Use: uv sync, uv run, uv pip, etc." -ForegroundColor Cyan

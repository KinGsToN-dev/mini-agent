# show_project.ps1
# Собирает структуру проекта и содержимое файлов для анализа.
# Запуск: .\show_project.ps1
# Если PowerShell блокирует запуск: powershell -ExecutionPolicy Bypass -File .\show_project.ps1

param(
    [string]$Root = ".",
    [string]$OutputFile = "project_dump.txt"
)

# Что игнорировать при обходе
$ExcludeDirs = @(
    ".venv", "venv", "env",
    "__pycache__", ".git", ".idea", ".vscode",
    "node_modules", ".mypy_cache", ".pytest_cache",
    "dist", "build", "*.egg-info"
)

# Какие расширения включать (текстовые файлы)
$IncludeExtensions = @(
    ".py", ".txt", ".md", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".env", ".gitignore",
    ".ps1", ".bat", ".cmd", ".sh"
)

# Файлы, которые включаем даже без расширения
$IncludeNames = @(
    ".env", ".gitignore", "Dockerfile", "Makefile",
    "requirements.txt", "pyproject.toml"
)

# Максимальный размер файла (в байтах) для дампа — чтобы не залить гигантские логи
$MaxFileSize = 200KB

function Test-Excluded {
    param([string]$Path)
    foreach ($ex in $ExcludeDirs) {
        if ($Path -like "*\$ex\*" -or $Path -like "*\$ex") { return $true }
    }
    return $false
}

function Test-Included {
    param([System.IO.FileInfo]$File)
    $ext = $File.Extension.ToLower()
    if ($IncludeExtensions -contains $ext) { return $true }
    if ($IncludeNames -contains $File.Name) { return $true }
    return $false
}

$RootFull = (Resolve-Path $Root).Path
$OutputPath = Join-Path $RootFull $OutputFile

# Очищаем/создаём выходной файл
"" | Out-File -FilePath $OutputPath -Encoding UTF8

function Write-Line {
    param([string]$Text = "")
    $Text | Out-File -FilePath $OutputPath -Encoding UTF8 -Append
}

Write-Line "================================================================"
Write-Line "PROJECT DUMP"
Write-Line "Root: $RootFull"
Write-Line "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Line "OS: $([System.Environment]::OSVersion.VersionString)"
Write-Line "PowerShell: $($PSVersionTable.PSVersion)"
Write-Line "================================================================"
Write-Line ""

# 1. ДЕРЕВО ПРОЕКТА
Write-Line "--- [1] PROJECT TREE ---"
Write-Line ""

$allFiles = Get-ChildItem -Path $RootFull -Recurse -File -Force |
    Where-Object { -not (Test-Excluded $_.FullName) }

$allDirs = Get-ChildItem -Path $RootFull -Recurse -Directory -Force |
    Where-Object { -not (Test-Excluded $_.FullName) }

$relDirs = $allDirs | ForEach-Object {
    $_.FullName.Substring($RootFull.Length).TrimStart('\')
} | Sort-Object

$relFiles = $allFiles | ForEach-Object {
    $_.FullName.Substring($RootFull.Length).TrimStart('\')
} | Sort-Object

Write-Line "Directories:"
foreach ($d in $relDirs) { Write-Line "  [D] $d" }
Write-Line ""
Write-Line "Files:"
foreach ($f in $relFiles) { Write-Line "  [F] $f" }
Write-Line ""

# 2. СОДЕРЖИМОЕ ФАЙЛОВ
Write-Line "--- [2] FILE CONTENTS ---"
Write-Line ""

foreach ($file in ($allFiles | Sort-Object FullName)) {
    if (-not (Test-Included $file)) { continue }

    $rel = $file.FullName.Substring($RootFull.Length).TrimStart('\')

    Write-Line "================================================================"
    Write-Line "FILE: $rel"
    Write-Line "Size: $($file.Length) bytes"
    Write-Line "Modified: $($file.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Line "================================================================"

    if ($file.Length -gt $MaxFileSize) {
        Write-Line "[SKIPPED] Файл больше $($MaxFileSize/1KB)KB"
        Write-Line ""
        continue
    }

    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop
        if ($null -eq $content) { $content = "" }
        Write-Line $content
    } catch {
        Write-Line "[ERROR] Не удалось прочитать: $($_.Exception.Message)"
    }
    Write-Line ""
}

# 3. ИНФО ОБ ОКРУЖЕНИИ
Write-Line "--- [3] ENVIRONMENT ---"
Write-Line ""

# Python
try {
    $pyVersion = & python --version 2>&1
    Write-Line "Python: $pyVersion"
} catch { Write-Line "Python: не найден" }

# pip freeze (если есть venv)
$venvPip = Join-Path $RootFull ".venv\Scripts\pip.exe"
if (Test-Path $venvPip) {
    Write-Line ""
    Write-Line "pip freeze (.venv):"
    try {
        & $venvPip freeze 2>&1 | ForEach-Object { Write-Line "  $_" }
    } catch { Write-Line "  [ERROR] $($_.Exception.Message)" }
} else {
    Write-Line "venv не найден в .venv"
}

# 4. ДЕРЕВО В ВИДЕ TREE (если есть утилита)
Write-Line ""
Write-Line "--- [4] TREE COMMAND OUTPUT ---"
Write-Line ""
try {
    $treeOut = & cmd /c "tree /F /A `"$RootFull`"" 2>&1
    $treeOut | ForEach-Object { Write-Line $_ }
} catch {
    Write-Line "[ERROR] tree: $($_.Exception.Message)"
}

Write-Line ""
Write-Line "================================================================"
Write-Line "END OF DUMP"
Write-Line "================================================================"

Write-Host ""
Write-Host "Готово!" -ForegroundColor Green
Write-Host "Файл: $OutputPath" -ForegroundColor Cyan
Write-Host "Размер: $([math]::Round((Get-Item $OutputPath).Length / 1KB, 1)) KB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Открой файл и скопируй содержимое сюда." -ForegroundColor Yellow
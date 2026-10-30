$ErrorActionPreference = "Stop"
Write-Host "=== 替换 Program Files 里的 chromedriver 为 155 ===" -ForegroundColor Cyan
$src  = "D:\personal-finance-tracker-api\tools\chromedriver.exe"
$dest = "C:\Program Files\Google\Chrome\Application\chromedriver.exe"
if (-not (Test-Path $src)) { throw "找不到新驱动: $src" }
$newVer = (& $src --version) -join ""
Write-Host "新驱动: $newVer"
if ($newVer -notmatch "155\.") { throw "版本不是 155，已停止" }
if (Test-Path $dest) {
    Copy-Item $dest "$dest.154.bak" -Force
    Write-Host "旧驱动已备份 -> chromedriver.exe.154.bak" -ForegroundColor Yellow
}
Copy-Item $src $dest -Force
Write-Host "已替换: $dest" -ForegroundColor Green
Write-Host "验证:" -ForegroundColor Cyan
& $dest --version
Write-Host "完成。可以关掉这个窗口了。" -ForegroundColor Green
Read-Host "按回车退出"

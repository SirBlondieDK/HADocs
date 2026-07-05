Write-Host "HADocs v1.0.0 release cleanup" -ForegroundColor Cyan

Write-Host "`nGit status:" -ForegroundColor Yellow
git status --short

Write-Host "`nUntracked/generated folders to check:" -ForegroundColor Yellow
$paths = @(
  ".pytest_tmp",
  ".pytest_cache",
  "__pycache__",
  "build",
  "dist",
  "output",
  "cache"
)

foreach ($p in $paths) {
  if (Test-Path $p) {
    Write-Host "Found: $p"
  }
}

Write-Host "`nTracked generated/sensitive files:" -ForegroundColor Yellow
git ls-files output cache dist build .pytest_cache .pytest_tmp local-config.json 2>$null

Write-Host "`nRun tests:" -ForegroundColor Yellow
py -3.14 -m pytest

Write-Host "`nSuggested release commands:" -ForegroundColor Green
Write-Host 'git add .'
Write-Host 'git commit -m "Prepare v1.0.0 release"'
Write-Host 'git tag -a v1.0.0 -m "HADocs v1.0.0"'
Write-Host 'git push'
Write-Host 'git push origin v1.0.0'

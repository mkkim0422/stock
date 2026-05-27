# pre-commit hook (참고)

실제 hook 활성은 Phase 7. 현재는 안내.

## 점검 항목
- ruff check
- pytest
- 키 누출 grep
- .env staging 차단

## Windows PowerShell 예시
```powershell
ruff check src/ tests/
if ($LASTEXITCODE -ne 0) { exit 1 }
py -m pytest tests/ -q
if ($LASTEXITCODE -ne 0) { exit 1 }
```

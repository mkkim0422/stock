---
name: backup-restore
description: SQLite DB 백업과 복원 절차
---

# backup-restore skill

## 백업 (수동)
```powershell
# 1) WAL 체크포인트 + VACUUM
py -c "import sqlite3; c=sqlite3.connect('data/db/swing.db'); c.execute('PRAGMA wal_checkpoint(FULL)'); c.execute('VACUUM'); c.close()"

# 2) 파일 복사
$d = Get-Date -Format "yyyyMMdd"
Copy-Item data/db/swing.db "data/backups/swing-$d.db"
```

## 백업 (자동, Phase 7)
- `.github/workflows/db-backup-weekly.yml`
- 주 1회 일요일

## 복원
```powershell
# 백업 파일에서 복원
Copy-Item data/backups/swing-20260520.db data/db/swing.db -Force
# WAL/SHM 잔재 제거
Remove-Item data/db/swing.db-wal -ErrorAction SilentlyContinue
Remove-Item data/db/swing.db-shm -ErrorAction SilentlyContinue
```

## 주의
- 복원 전 현재 DB 백업 권장
- Streamlit/다른 프로세스 종료 후 복원
- 백업 보존: 8주 (이후 자동 삭제, Phase 7)

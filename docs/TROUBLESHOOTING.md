# TROUBLESHOOTING — 문제 해결

## Streamlit 실행 안 됨
- `pip install streamlit` 확인
- `streamlit run src/ui/app.py` 절대경로로
- 포트 충돌: `--server.port 8502`
- 한국어 파일명 페이지 → 영문 prefix 사용

## pytest 실패
- `pip install -r requirements-dev.txt`
- `PYTHONPATH` 자동: pytest는 `conftest.py` 위치 기준
- 캐시 정리: `python -m pytest --cache-clear`

## SQLite "database is locked"
- WAL 모드 확인 (`PRAGMA journal_mode=WAL`)
- 다른 프로세스에서 쓰기 중인지
- `.db-shm`, `.db-wal` 잔재 삭제 후 재시도

## ruff/mypy 에러
- ruff: `ruff check src/ tests/ --fix`
- mypy: 점진적 도입, `# type: ignore[code]` 정밀하게

## yfinance 429/타임아웃 (Phase 2)
- tenacity 지수 백오프
- FinanceDataReader 폴백
- 마지막 캐시 사용

## GitHub Actions cron 발화 안 됨
- 15~30분 지연은 정상
- 1시간+ 지연: GitHub status 확인
- private repo 무료 한도 (월 2,000분) 초과 여부

## Streamlit Cloud sleep
- 12시간 비활성 후 sleep
- keepalive-weekly.yml 활성 확인 (Phase 7)

## API 키 누출
- 즉시 발급처 revoke
- `git filter-repo`로 히스토리 정리
- docs/SECURITY.md 참고

## Python 3.14 wheel 없음
- 일부 패키지(특히 pandas/numpy 신버전)는 3.14 wheel 미배포 가능
- 해결: 3.11 또는 3.12 사용 권장
- 또는 소스 빌드 (`pip install --no-binary :all: pandas` — 느림)

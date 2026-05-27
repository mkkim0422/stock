# swing-advisor

한국+미국 스윙 트레이딩 보조 도구 (페이퍼 트레이딩 전용).

## 빠른 시작

```powershell
# 1. 가상환경
py -m venv .venv
.venv\Scripts\activate

# 2. 의존성
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. 환경변수 (Phase 1은 비워둬도 작동)
copy .env.example .env

# 4. UI 실행
streamlit run src/ui/app.py

# 5. 테스트
pytest -v --cov=src
```

## 면책
본 도구는 페이퍼 트레이딩 전용이며 실거래 결과를 보장하지 않는다.
모든 투자 책임은 사용자 본인에게 있다.

상세는 [CLAUDE.md](./CLAUDE.md) 와 [docs/](./docs/) 참고.

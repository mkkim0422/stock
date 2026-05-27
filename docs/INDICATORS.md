# INDICATORS — 기술 지표 (직접 구현)

## 원칙
- **pandas-ta / ta-lib 의존 금지**.
- numpy + pandas로 직접 구현.
- 단위 테스트로 알려진 값과 비교.

## RSI(n)
```
delta = price.diff()
gain = delta.clip(lower=0).rolling(n).mean()
loss = (-delta.clip(upper=0)).rolling(n).mean()
rs = gain / loss
rsi = 100 - 100 / (1 + rs)
```
n=14 기본.

## MACD
```
ema_fast = ewm(span=12, adjust=False).mean()
ema_slow = ewm(span=26, adjust=False).mean()
macd = ema_fast - ema_slow
signal = macd.ewm(span=9, adjust=False).mean()
hist = macd - signal
```

## 이동평균
- SMA(n): `rolling(n).mean()`
- EMA(n): `ewm(span=n, adjust=False).mean()`
- 자주 쓰는 n: 5, 20, 60, 120, 200

## 거래량 지표 (Phase 3)
- VR (Volume Ratio)
- OBV (On-Balance Volume)

## 사용 주의
- look-ahead 방지: `shift(1)` 또는 `closed='left'` 적용
- 거래일 갭 처리: 영업일 인덱스 유지
- NaN 첫 n-1 봉 처리

"""Toss-inspired 디자인 시스템 — 전역 CSS + 카드 헬퍼.

한국 주식 문화 색상(빨강=상승, 파랑=하락)을 따른다.
"""
from __future__ import annotations

import streamlit as st

# 색상 토큰
COLOR_BG = "#FAFBFC"
COLOR_CARD = "#FFFFFF"
COLOR_BORDER = "#F2F4F6"
COLOR_TEXT = "#191F28"
COLOR_SUBTLE = "#6B7684"
COLOR_BRAND = "#3182F6"
COLOR_BRAND_HOVER = "#1B64DA"
COLOR_UP = "#FF4040"      # 빨강 = 상승 (한국 주식 컨벤션)
COLOR_DOWN = "#3282F6"    # 파랑 = 하락
COLOR_NEUTRAL = "#8B95A1"

_CSS = """
<style>
/* ── Base ── */
.stApp { background: %BG%; }
.stApp, .stApp p, .stApp span, .stApp div { color: %TEXT%; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { background: transparent !important; }

/* ── 타이틀 — 토스는 헤딩 두껍게 ── */
h1 { font-weight: 800 !important; letter-spacing: -0.02em; }
h2, h3 { font-weight: 700 !important; letter-spacing: -0.01em; }

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: %CARD% !important;
    border-right: 1px solid %BORDER% !important;
}
section[data-testid="stSidebar"] > div { padding-top: 8px; }

/* ── 토스 카드 ── */
.toss-card {
    background: %CARD%;
    border-radius: 16px;
    padding: 20px 22px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    margin-bottom: 14px;
    border: 1px solid %BORDER%;
}
.toss-card-tight {
    background: %CARD%;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    border: 1px solid %BORDER%;
}

/* 카드 안 큰 숫자 / 레이블 */
.toss-label {
    font-size: 13px;
    color: %SUBTLE%;
    margin: 0 0 6px 0;
    font-weight: 500;
}
.toss-value {
    font-size: 28px;
    font-weight: 800;
    color: %TEXT%;
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin: 0;
}
.toss-value-md {
    font-size: 20px;
    font-weight: 700;
    color: %TEXT%;
    line-height: 1.2;
    margin: 0;
}
.toss-sub {
    font-size: 13px;
    color: %SUBTLE%;
    margin: 4px 0 0 0;
}
.toss-up { color: %UP% !important; font-weight: 700; }
.toss-down { color: %DOWN% !important; font-weight: 700; }
.toss-neutral { color: %NEUTRAL% !important; }

/* 추천 카드 */
.toss-rec-card {
    background: %CARD%;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 12px;
    border: 1px solid %BORDER%;
    box-shadow: 0 2px 6px rgba(0,0,0,0.03);
}
.toss-rec-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
}
.toss-rec-name { font-size: 17px; font-weight: 700; }
.toss-rec-code { font-size: 13px; color: %SUBTLE%; margin-left: 6px; }
.toss-rec-score { font-size: 22px; font-weight: 800; }
.toss-rec-comment { font-size: 14px; color: %TEXT%; line-height: 1.5; margin-top: 6px; }
.toss-rec-meta { font-size: 12px; color: %SUBTLE%; margin-top: 6px; }

/* 배지 */
.toss-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
}
.toss-badge-buy { background: rgba(255,64,64,0.10); color: %UP%; }
.toss-badge-sell { background: rgba(50,130,246,0.10); color: %DOWN%; }
.toss-badge-hold { background: rgba(139,149,161,0.10); color: %NEUTRAL%; }

/* ── 버튼 ── */
.stButton > button {
    background: %BRAND% !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 20px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    box-shadow: 0 1px 3px rgba(49,130,246,0.20);
    transition: background 0.15s ease;
}
.stButton > button:hover { background: %BRAND_HOVER% !important; }
.stButton > button:disabled {
    background: #E5E8EB !important;
    color: #B0B8C1 !important;
    box-shadow: none;
}
/* secondary (kind=secondary) — 회색 */
.stButton > button[kind="secondary"] {
    background: %BORDER% !important;
    color: %TEXT% !important;
    box-shadow: none;
}
.stButton > button[kind="secondary"]:hover { background: #E5E8EB !important; }

/* page_link 버튼 */
a[data-testid="stPageLink-NavLink"] {
    background: %CARD% !important;
    border: 1px solid %BORDER% !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    margin-bottom: 6px !important;
}
a[data-testid="stPageLink-NavLink"]:hover {
    background: %BG% !important;
    border-color: %BRAND% !important;
}

/* metric 위젯 — 토스 느낌 */
[data-testid="stMetric"] {
    background: %CARD%;
    padding: 16px 18px;
    border-radius: 14px;
    border: 1px solid %BORDER%;
}
[data-testid="stMetricLabel"] {
    font-size: 13px !important;
    color: %SUBTLE% !important;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    font-size: 24px !important;
    font-weight: 800 !important;
    color: %TEXT% !important;
    letter-spacing: -0.01em;
}

/* expander */
[data-testid="stExpander"] {
    background: %CARD%;
    border-radius: 14px;
    border: 1px solid %BORDER% !important;
}

/* dataframe */
[data-testid="stDataFrame"] {
    border-radius: 14px;
    border: 1px solid %BORDER%;
    overflow: hidden;
}

/* input */
[data-baseweb="input"] > div, [data-baseweb="select"] > div {
    border-radius: 12px !important;
    border-color: %BORDER% !important;
}

/* alert/info/warning/success */
[data-testid="stAlert"] {
    border-radius: 14px !important;
    border: none !important;
}

/* caption */
.stCaption, [data-testid="stCaptionContainer"] {
    color: %SUBTLE% !important;
}
</style>
"""


def inject_css() -> None:
    """모든 페이지 첫 줄에서 호출해 토스 테마 적용."""
    css = (
        _CSS
        .replace("%BG%", COLOR_BG)
        .replace("%CARD%", COLOR_CARD)
        .replace("%BORDER%", COLOR_BORDER)
        .replace("%TEXT%", COLOR_TEXT)
        .replace("%SUBTLE%", COLOR_SUBTLE)
        .replace("%BRAND_HOVER%", COLOR_BRAND_HOVER)
        .replace("%BRAND%", COLOR_BRAND)
        .replace("%UP%", COLOR_UP)
        .replace("%DOWN%", COLOR_DOWN)
        .replace("%NEUTRAL%", COLOR_NEUTRAL)
    )
    st.markdown(css, unsafe_allow_html=True)


def big_number(
    label: str,
    value: str,
    sub: str | None = None,
    trend: str | None = None,
) -> str:
    """토스 스타일 큰 숫자 카드 HTML.

    trend: 'up' | 'down' | None — sub 텍스트 색상.
    """
    klass = "toss-sub"
    if trend == "up":
        klass = "toss-sub toss-up"
    elif trend == "down":
        klass = "toss-sub toss-down"
    sub_html = f'<p class="{klass}">{sub}</p>' if sub else ""
    return f"""
<div class="toss-card">
  <p class="toss-label">{label}</p>
  <p class="toss-value">{value}</p>
  {sub_html}
</div>
"""


def render_big_number(
    label: str,
    value: str,
    sub: str | None = None,
    trend: str | None = None,
) -> None:
    st.markdown(big_number(label, value, sub, trend), unsafe_allow_html=True)


def card(body_html: str) -> None:
    """임의 HTML 을 토스 카드로 감싸기."""
    st.markdown(f'<div class="toss-card">{body_html}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "hold") -> str:
    """추천 배지: kind in {'buy','sell','hold'}."""
    return f'<span class="toss-badge toss-badge-{kind}">{text}</span>'


def recommendation_card(
    name: str,
    code: str,
    score: int,
    comment: str,
    action: str,  # 'buy' | 'sell' | 'hold'
    extra: str | None = None,
) -> None:
    """🎯 오늘의 추천 페이지의 종목 카드."""
    if action == "buy":
        score_cls = "toss-up"
        badge_html = badge("매수 후보", "buy")
    elif action == "sell":
        score_cls = "toss-down"
        badge_html = badge("매도 후보", "sell")
    else:
        score_cls = "toss-neutral"
        badge_html = badge("보류", "hold")

    score_str = f"+{score}" if score > 0 else str(score)
    extra_html = f'<p class="toss-rec-meta">{extra}</p>' if extra else ""

    html = f"""
<div class="toss-rec-card">
  <div class="toss-rec-head">
    <div>
      <span class="toss-rec-name">{name}</span>
      <span class="toss-rec-code">{code}</span>
    </div>
    <div>
      <span class="toss-rec-score {score_cls}">{score_str}점</span>
    </div>
  </div>
  <div>{badge_html}</div>
  <p class="toss-rec-comment">{comment}</p>
  {extra_html}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)

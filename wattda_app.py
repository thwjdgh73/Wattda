import streamlit as st
import pandas as pd
import numpy as np
from datetime import time
import io
import os
import html
import base64
import re
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except Exception:
    FOLIUM_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


# ============================================================
# Page setup
# ============================================================

st.set_page_config(
    page_title="Wattda | 전기요금 진단 AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Korean font setup
# ============================================================

def find_font_path():
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


FONT_PATH = find_font_path()
if FONT_PATH:
    try:
        font_name = fm.FontProperties(fname=FONT_PATH).get_name()
        plt.rcParams["font.family"] = font_name
    except Exception:
        pass
plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# UI styling
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1220px;
    }

    section[data-testid="stSidebar"] {
        background: #0F172A;
    }

    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    .w-hero {
        position: relative;
        padding: 30px 32px;
        border-radius: 26px;
        background:
            radial-gradient(circle at 20% 20%, rgba(96,165,250,0.28), transparent 34%),
            linear-gradient(135deg, #0F172A 0%, #111827 50%, #1E293B 100%);
        color: white;
        margin-bottom: 18px;
        box-shadow: 0 14px 34px rgba(15,23,42,0.18);
    }

    .w-hero h1 {
        font-size: 46px;
        margin: 0 0 8px 0;
        letter-spacing: -0.04em;
        line-height: 1.08;
    }

    .w-hero p {
        font-size: 17px;
        margin: 0;
        color: rgba(255,255,255,0.88);
        line-height: 1.65;
    }

    .w-title-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 16px;
    }

    .w-author {
        font-size: 12px;
        color: rgba(255,255,255,0.72);
        letter-spacing: -0.01em;
        white-space: nowrap;
        padding-top: 8px;
    }

    .w-badge {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.13);
        border: 1px solid rgba(255,255,255,0.22);
        color: white;
        font-size: 13px;
        margin-bottom: 13px;
    }

    .w-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 8px 22px rgba(15,23,42,0.05);
    }

    .w-card h3 {
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 18px;
        letter-spacing: -0.02em;
    }

    .w-muted {
        color: #6B7280;
        font-size: 14px;
        line-height: 1.6;
    }

    .w-pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #EFF6FF;
        color: #1D4ED8;
        font-size: 13px;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .w-summary-box {
        border-left: 5px solid #2563EB;
        background: #EFF6FF;
        padding: 14px 16px;
        border-radius: 12px;
        margin: 12px 0;
        color: #1E3A8A;
    }

    .stMetric {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 14px 16px;
        border-radius: 18px;
        box-shadow: 0 8px 20px rgba(15,23,42,0.04);
    }

    div[data-testid="stMetricValue"] {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    div[data-testid="stMetricLabel"] {
        color: #6B7280;
    }

    .w-money-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 8px 20px rgba(15,23,42,0.04);
        min-height: 92px;
    }

    .w-money-label {
        font-size: 13px;
        color: #6B7280;
        margin-bottom: 8px;
    }

    .w-money-value {
        font-size: 26px;
        font-weight: 850;
        line-height: 1.35;
        letter-spacing: -0.02em;
        color: #111827;
        white-space: normal;
        word-break: keep-all;
    }


    .w-app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        padding: 24px 28px;
        border-radius: 26px;
        background:
            radial-gradient(circle at 18% 20%, rgba(96,165,250,0.22), transparent 34%),
            linear-gradient(135deg, #0F172A 0%, #111827 50%, #1E293B 100%);
        color: white;
        box-shadow: 0 14px 34px rgba(15,23,42,0.16);
        margin-bottom: 18px;
    }

    .w-app-header h1 {
        margin: 2px 0 6px 0;
        font-size: 38px;
        line-height: 1.1;
        letter-spacing: -0.04em;
    }

    .w-app-header p {
        margin: 0;
        color: rgba(255,255,255,0.82);
        font-size: 15px;
        line-height: 1.6;
    }

    .w-app-kicker {
        font-size: 12px;
        font-weight: 800;
        color: #BFDBFE;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .w-app-status {
        white-space: nowrap;
        border: 1px solid rgba(255,255,255,0.22);
        background: rgba(255,255,255,0.12);
        border-radius: 999px;
        padding: 8px 12px;
        color: rgba(255,255,255,0.88);
        font-size: 13px;
        font-weight: 800;
    }

    .w-stepbar {
        display: flex;
        gap: 10px;
        margin: 8px 0 22px 0;
    }

    .w-step, .w-step-active {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 10px;
        border-radius: 999px;
        padding: 10px 14px;
        border: 1px solid #E5E7EB;
        background: #FFFFFF;
        color: #64748B;
        font-weight: 800;
        font-size: 14px;
    }

    .w-step span, .w-step-active span {
        display: inline-grid;
        place-items: center;
        width: 26px;
        height: 26px;
        border-radius: 999px;
        background: #E5E7EB;
        color: #334155;
        font-size: 13px;
    }

    .w-step-active {
        border-color: #2563EB;
        background: #EFF6FF;
        color: #1D4ED8;
    }

    .w-step-active span {
        background: #2563EB;
        color: #FFFFFF;
    }

    .w-action-card {
        border: 1px solid #E5E7EB;
        border-radius: 24px;
        padding: 22px;
        background: #FFFFFF;
        box-shadow: 0 12px 28px rgba(15,23,42,0.06);
        min-height: 122px;
        margin-bottom: 12px;
    }

    .w-action-title {
        font-size: 21px;
        font-weight: 900;
        letter-spacing: -0.03em;
        color: #0F172A;
        margin-bottom: 8px;
    }

    .w-action-desc {
        color: #64748B;
        font-size: 15px;
        line-height: 1.6;
    }


    .w-form-section {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 22px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 22px rgba(15,23,42,0.04);
    }

    .w-form-section-title {
        font-size: 18px;
        font-weight: 900;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
        color: #0F172A;
    }

    .w-form-section-desc {
        color: #64748B;
        font-size: 13px;
        margin-bottom: 14px;
        line-height: 1.55;
    }

    .w-small-note {
        color: #64748B;
        font-size: 13px;
        line-height: 1.55;
    }

    .w-location-chip {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: #F1F5F9;
        color: #334155;
        font-size: 12px;
        font-weight: 700;
        margin-top: 6px;
    }


    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(255,255,255,0.10) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 12px !important;
        padding: 10px 12px !important;
        margin: 7px 0 !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #F8FAFC !important;
        font-weight: 800 !important;
        font-size: 14px !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: #FF4B4B !important;
        border-color: #FF4B4B !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.16) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Column names
# ============================================================

COL_DT = "일시"
COL_KWH = "전력사용량(kWh)"
COL_OUT = "실외온도(°C)"
COL_IN = "실내온도(°C)"
COL_RH = "상대습도(%)"
COL_OCC = "점유인원(명)"


# ============================================================
# Formatting helpers
# ============================================================

def krw(value):
    try:
        return f"{int(round(float(value))):,}원"
    except Exception:
        return "0원"


def kwh(value):
    try:
        return f"{float(value):,.1f} kWh"
    except Exception:
        return "0.0 kWh"


def pct(value):
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "0.0%"


def money_card(label, value):
    st.markdown(
        f"""
        <div class="w-money-card">
            <div class="w-money-label">{label}</div>
            <div class="w-money-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_div(a, b, default=0):
    try:
        if b == 0 or pd.isna(b):
            return default
        return a / b
    except Exception:
        return default


# ============================================================
# Professional KPI and data quality helpers
# ============================================================

def number1(value, suffix=""):
    try:
        return f"{float(value):,.1f}{suffix}"
    except Exception:
        return f"0.0{suffix}"


def estimate_interval_hours(df):
    try:
        tmp = df[[COL_DT]].dropna().sort_values(COL_DT).copy()
        diffs = tmp[COL_DT].diff().dropna().dt.total_seconds() / 3600
        if len(diffs) == 0:
            return 1.0
        median_hours = float(diffs.median())
        if median_hours <= 0 or pd.isna(median_hours):
            return 1.0
        return median_hours
    except Exception:
        return 1.0


def data_quality_summary(raw_df):
    """
    Basic data quality screening for an energy diagnosis app.

    Checks:
    - required columns
    - timestamp parse quality
    - numeric kWh parse quality
    - duplicated timestamps
    - missing time intervals
    - negative kWh values
    - high outliers
    - optional diagnostic columns
    """
    df = raw_df.copy()
    messages = []
    warnings = []
    score = 100

    required_cols = [COL_DT, COL_KWH]
    missing_required = [c for c in required_cols if c not in df.columns]
    optional_cols = [COL_OUT, COL_IN, COL_RH, COL_OCC]
    present_optional = [c for c in optional_cols if c in df.columns]
    missing_optional = [c for c in optional_cols if c not in df.columns]

    if missing_required:
        score -= 45
        warnings.append(f"필수 컬럼 누락: {', '.join(missing_required)}")
        return {
            "score": max(0, score),
            "grade": "낮음",
            "messages": messages,
            "warnings": warnings,
            "missing_required": missing_required,
            "present_optional": present_optional,
            "missing_optional": missing_optional,
            "duplicate_count": 0,
            "missing_intervals": None,
            "negative_count": None,
            "outlier_count": None,
            "valid_rows": 0,
            "total_rows": len(df),
        }

    total_rows = len(df)
    ts = pd.to_datetime(df[COL_DT], errors="coerce")
    kwh_series = pd.to_numeric(df[COL_KWH], errors="coerce")

    invalid_ts = int(ts.isna().sum())
    invalid_kwh = int(kwh_series.isna().sum())
    valid_mask = ts.notna() & kwh_series.notna()
    valid_rows = int(valid_mask.sum())

    if total_rows == 0:
        score -= 70
        warnings.append("데이터 행이 없습니다.")
    else:
        invalid_ratio = safe_div(invalid_ts + invalid_kwh, total_rows * 2, 0)
        if invalid_ratio > 0.10:
            score -= 25
        elif invalid_ratio > 0.03:
            score -= 12

    if invalid_ts > 0:
        warnings.append(f"날짜로 해석되지 않은 행: {invalid_ts}개")
    if invalid_kwh > 0:
        warnings.append(f"전력사용량이 숫자로 해석되지 않은 행: {invalid_kwh}개")

    clean = pd.DataFrame({COL_DT: ts, COL_KWH: kwh_series}).dropna().sort_values(COL_DT)

    duplicate_count = int(clean[COL_DT].duplicated().sum())
    if duplicate_count > 0:
        score -= min(15, 5 + duplicate_count)
        warnings.append(f"중복 타임스탬프: {duplicate_count}개")

    negative_count = int((clean[COL_KWH] < 0).sum())
    if negative_count > 0:
        score -= min(20, 8 + negative_count)
        warnings.append(f"음수 전력사용량: {negative_count}개")

    outlier_count = 0
    if len(clean) >= 20:
        q1 = clean[COL_KWH].quantile(0.25)
        q3 = clean[COL_KWH].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            upper = q3 + 3.0 * iqr
            outlier_count = int((clean[COL_KWH] > upper).sum())
            if outlier_count > 0:
                score -= min(10, outlier_count)
                warnings.append(f"상위 이상치 후보: {outlier_count}개")

    missing_intervals = None
    if len(clean) >= 3:
        diffs = clean[COL_DT].diff().dropna()
        median_delta = diffs.median()
        if pd.notna(median_delta) and median_delta.total_seconds() > 0:
            expected = pd.date_range(clean[COL_DT].min(), clean[COL_DT].max(), freq=median_delta)
            missing_intervals = max(0, len(expected) - clean[COL_DT].nunique())
            if missing_intervals > 0:
                missing_ratio = safe_div(missing_intervals, len(expected), 0)
                if missing_ratio > 0.10:
                    score -= 20
                elif missing_ratio > 0.03:
                    score -= 10
                else:
                    score -= 4
                warnings.append(f"추정 누락 시간 구간: {missing_intervals}개")

    if len(present_optional) >= 3:
        messages.append("실외온도, 실내온도, 습도 또는 점유 데이터가 포함되어 있어 진단 해석력이 높습니다.")
    elif len(present_optional) >= 1:
        messages.append("일부 권장 컬럼이 포함되어 있으나, 점유·실내환경 기반 진단은 제한적으로 해석해야 합니다.")
        score -= 4
    else:
        warnings.append("권장 컬럼이 없어 냉방·쾌적성·점유 기반 진단의 신뢰도가 제한됩니다.")
        score -= 10

    score = int(max(0, min(100, round(score))))

    if score >= 85:
        grade = "높음"
    elif score >= 70:
        grade = "보통"
    elif score >= 55:
        grade = "주의"
    else:
        grade = "낮음"

    if not warnings:
        messages.append("필수 데이터 구조와 시간축 품질이 전반적으로 양호합니다.")

    return {
        "score": score,
        "grade": grade,
        "messages": messages,
        "warnings": warnings,
        "missing_required": missing_required,
        "present_optional": present_optional,
        "missing_optional": missing_optional,
        "duplicate_count": duplicate_count,
        "missing_intervals": missing_intervals,
        "negative_count": negative_count,
        "outlier_count": outlier_count,
        "valid_rows": valid_rows,
        "total_rows": total_rows,
    }


def professional_kpis(info, result):
    df = result["df"].copy()
    floor_area = max(float(info.get("연면적", 0) or 0), 1.0)
    contract_kw = max(float(info.get("계약전력", 0) or 0), 0.0)

    period_days = max(1, (df[COL_DT].max() - df[COL_DT].min()).days + 1)
    total_kwh = float(df[COL_KWH].sum())
    annualized_kwh = total_kwh * 365 / period_days
    electric_eui = annualized_kwh / floor_area

    avg_kw = float(df[COL_KWH].mean())
    peak_kw = float(df[COL_KWH].max())
    load_factor = safe_div(avg_kw, peak_kw, 0) * 100

    base_threshold = df[COL_KWH].quantile(0.10)
    base_avg = float(df.loc[df[COL_KWH] <= base_threshold, COL_KWH].mean()) if len(df) > 0 else 0
    baseload_ratio = safe_div(base_avg, avg_kw, 0) * 100

    contract_utilization = safe_div(peak_kw, contract_kw, 0) * 100 if contract_kw > 0 else 0

    peak_hour_counts = df.sort_values(COL_KWH, ascending=False).head(max(10, min(50, len(df))))["시간"].value_counts()
    repeated_peak_hour = int(peak_hour_counts.idxmax()) if len(peak_hour_counts) else int(result["peak"]["시간"])

    if load_factor < 35:
        load_factor_comment = "피크 집중도가 높아 부하이동 또는 계약전력 검토 여지가 있습니다."
    elif load_factor < 55:
        load_factor_comment = "피크가 일부 시간대에 집중되는 편입니다."
    else:
        load_factor_comment = "평균 부하와 피크 부하의 차이가 비교적 안정적입니다."

    if baseload_ratio >= 55:
        baseload_comment = "상시부하 비중이 높아 야간·대기전력·상시가동 설비 점검이 필요합니다."
    elif baseload_ratio >= 40:
        baseload_comment = "기저부하가 다소 높은 편입니다."
    else:
        baseload_comment = "기저부하 비중은 상대적으로 낮은 편입니다."

    if contract_kw <= 0:
        contract_comment = "계약전력 정보가 부족해 계약전력 사용률을 판단할 수 없습니다."
    elif contract_utilization < 45:
        contract_comment = "계약전력 대비 피크가 낮아 최근 12개월 피크를 기준으로 계약전력 조정 가능성을 검토할 수 있습니다."
    elif contract_utilization > 95:
        contract_comment = "피크가 계약전력에 매우 근접합니다. 피크 관리와 초과 위험 점검이 필요합니다."
    else:
        contract_comment = "계약전력 대비 피크 사용률이 중간 범위입니다."

    return {
        "period_days": period_days,
        "annualized_kwh": annualized_kwh,
        "electric_eui": electric_eui,
        "avg_kw": avg_kw,
        "peak_kw": peak_kw,
        "load_factor": load_factor,
        "baseload_ratio": baseload_ratio,
        "base_avg": base_avg,
        "contract_utilization": contract_utilization,
        "repeated_peak_hour": repeated_peak_hour,
        "load_factor_comment": load_factor_comment,
        "baseload_comment": baseload_comment,
        "contract_comment": contract_comment,
    }


def confidence_from_quality(result, dq):
    score = int(dq.get("score", 0))
    if score >= 85 and result["cooling_sensitivity"] is not None:
        return "높음"
    if score >= 70:
        return "보통"
    if score >= 55:
        return "주의"
    return "낮음"


def recommendation_rows_professional(info, result):
    dq = data_quality_summary(result["df"])
    confidence = confidence_from_quality(result, dq)
    rows = []

    def add(action, effect, difficulty, required_data, verification, category="즉시 실행 가능"):
        rows.append({
            "구분": category,
            "우선순위": len(rows) + 1,
            "개선 조치": action,
            "예상 효과": effect,
            "난이도": difficulty,
            "진단 신뢰도": confidence,
            "필요 추가 데이터": required_data,
            "검증 방법": verification,
        })

    if result["night_ratio"] >= 35:
        add(
            "영업 종료 후 조명, 간판, 콘센트, 환기팬, 시스템에어컨 종료 상태 점검",
            "중간~높음" if result["night_ratio"] >= 45 else "중간",
            "낮음",
            "설비별 서브미터 또는 종료 체크리스트가 있으면 원인 식별 가능",
            "개선 전후 야간 평균 kWh/h와 야간 사용비율 비교",
        )

    if result["weekend_ratio"] >= 40:
        add(
            "휴무일 냉방, 조명, 간판, 환기 스케줄 분리",
            "중간~높음",
            "낮음",
            "휴무일 실제 운영 이벤트 로그",
            "개선 전후 주말/평일 사용비율 비교",
        )

    if result["cooling_sensitivity"] is not None and result["cooling_sensitivity"] >= 3:
        add(
            "오후 피크 시간대 냉방 설정온도와 공간별 운전 스케줄 조정",
            "중간",
            "중간",
            "실내온도, 실외온도, 냉방 운전상태, 공간별 점유 데이터",
            "유사 외기온 조건에서 14~17시 kWh와 실내온도 비교",
        )

    if result["low_occupancy_ratio"] is not None and result["low_occupancy_ratio"] >= 65:
        add(
            "저점유 시간대 부분 운전 또는 구역별 운전 검토",
            "중간",
            "중간",
            "공간별 점유, 조명 회로, 냉방 구역 데이터",
            "점유 대비 kWh 지표와 저점유 시간 평균 부하 비교",
        )

    add(
        "피크 Top 5 시간대의 실제 설비 운전 상태 확인",
        "중간",
        "낮음",
        "피크 시간대 설비 운전 기록 또는 현장 점검표",
        "반복 피크 시간대와 최대 kWh 감소 여부 비교",
    )

    add(
        "CO₂ 또는 점유 센서 기반 환기·냉방 제어 가능성 검토",
        "중간~높음",
        "중간",
        "CO₂, 점유, 외기댐퍼, 팬 운전 데이터",
        "개선 전후 환기 관련 전력과 IAQ 지표 동시 비교",
        category="추가 데이터 필요",
    )

    add(
        "계약전력과 피크수요의 적정성 검토",
        "요금 절감 중심",
        "낮음",
        "최근 12개월 최대수요, 요금청구서, 계약전력 이력",
        "계약전력 조정 전후 기본요금과 초과 위험 비교",
        category="요금 최적화",
    )

    return pd.DataFrame(rows)


def render_data_quality_box(result):
    dq = data_quality_summary(result["df"])
    st.markdown("### 데이터 품질 요약")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("데이터 품질 점수", f"{dq['score']}/100")
    q2.metric("진단 신뢰도", dq["grade"])
    q3.metric("유효 행 수", f"{dq['valid_rows']:,}개")
    q4.metric("권장 컬럼", f"{len(dq['present_optional'])}/4개")

    if dq["messages"]:
        for msg in dq["messages"]:
            st.success(msg)
    if dq["warnings"]:
        for msg in dq["warnings"]:
            st.warning(msg)

    return dq



# ============================================================
# Korea map location picker and real-time weather helpers
# ============================================================

KOREA_BOUNDS = {
    "min_lat": 33.0,
    "max_lat": 39.5,
    "min_lon": 124.0,
    "max_lon": 132.0,
}

KOREA_CITY_CENTERS = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
    "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114),
    "세종": (36.4800, 127.2890),
    "수원": (37.2636, 127.0286),
    "성남": (37.4200, 127.1265),
    "고양": (37.6584, 126.8320),
    "용인": (37.2411, 127.1776),
    "청주": (36.6424, 127.4890),
    "천안": (36.8151, 127.1139),
    "전주": (35.8242, 127.1480),
    "포항": (36.0190, 129.3435),
    "창원": (35.2270, 128.6811),
    "제주": (33.4996, 126.5312),
}


def clamp_korea_location(lat, lon, fallback_city="서울"):
    fallback_lat, fallback_lon = KOREA_CITY_CENTERS.get(fallback_city, KOREA_CITY_CENTERS["서울"])
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return fallback_lat, fallback_lon

    if not (KOREA_BOUNDS["min_lat"] <= lat <= KOREA_BOUNDS["max_lat"]):
        lat = fallback_lat
    if not (KOREA_BOUNDS["min_lon"] <= lon <= KOREA_BOUNDS["max_lon"]):
        lon = fallback_lon

    return lat, lon


def render_korea_city_location_picker(info):
    """
    한국 지도에서 건물 위치를 클릭해 위도와 경도를 선택합니다.
    folium 또는 streamlit-folium이 설치되어 있지 않으면 도시 중심 좌표 선택 방식으로 대체됩니다.
    """
    st.markdown("#### 지도에서 건물 위치 선택")
    st.caption("도시를 먼저 선택한 뒤, 지도에서 건물 위치를 클릭하세요. 선택 좌표는 실시간 기상정보 조회에 사용됩니다.")

    city_names = list(KOREA_CITY_CENTERS.keys())
    default_city = info.get("지도기준도시", "서울")
    if default_city not in city_names:
        default_city = "서울"

    selected_city = st.selectbox(
        "지도 기준 도시",
        city_names,
        index=city_names.index(default_city),
        help="지도 시작 위치를 정하는 기준 도시입니다.",
    )

    center_lat, center_lon = KOREA_CITY_CENTERS[selected_city]
    current_lat, current_lon = clamp_korea_location(
        info.get("위도", center_lat),
        info.get("경도", center_lon),
        selected_city,
    )

    if not FOLIUM_AVAILABLE:
        st.warning(
            "지도 선택 기능을 사용하려면 requirements.txt에 folium과 streamlit-folium을 추가해야 합니다. "
            "현재는 선택한 도시 중심 좌표를 사용합니다."
        )
        loc_cols = st.columns(2)
        loc_cols[0].metric("선택 위도", f"{center_lat:.5f}")
        loc_cols[1].metric("선택 경도", f"{center_lon:.5f}")
        return selected_city, center_lat, center_lon

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB positron",
        max_bounds=True,
        min_lat=KOREA_BOUNDS["min_lat"],
        max_lat=KOREA_BOUNDS["max_lat"],
        min_lon=KOREA_BOUNDS["min_lon"],
        max_lon=KOREA_BOUNDS["max_lon"],
    )

    folium.Marker(
        location=[current_lat, current_lon],
        tooltip="현재 선택 위치",
        popup=f"현재 선택 위치: {current_lat:.5f}, {current_lon:.5f}",
        icon=folium.Icon(color="blue", icon="home"),
    ).add_to(m)

    map_data = st_folium(
        m,
        height=430,
        width=None,
        returned_objects=["last_clicked"],
        key=f"korea_location_picker_{selected_city}",
    )

    selected_lat = current_lat
    selected_lon = current_lon

    if map_data and map_data.get("last_clicked"):
        clicked_lat = float(map_data["last_clicked"]["lat"])
        clicked_lon = float(map_data["last_clicked"]["lng"])

        if (
            KOREA_BOUNDS["min_lat"] <= clicked_lat <= KOREA_BOUNDS["max_lat"]
            and KOREA_BOUNDS["min_lon"] <= clicked_lon <= KOREA_BOUNDS["max_lon"]
        ):
            selected_lat = clicked_lat
            selected_lon = clicked_lon
        else:
            st.warning("한국 영역 안의 위치를 선택해 주세요.")

    loc_cols = st.columns(2)
    loc_cols[0].metric("선택 위도", f"{selected_lat:.5f}")
    loc_cols[1].metric("선택 경도", f"{selected_lon:.5f}")

    return selected_city, selected_lat, selected_lon


def get_openweather_api_key():
    try:
        return st.secrets["OPENWEATHER_API_KEY"]
    except Exception:
        return None


def normalize_korea_address_query(address):
    """
    Clean Korean address text for geocoding.
    The app uses OpenStreetMap Nominatim first because detailed Korean road addresses
    are often not resolved well by OpenWeather's direct geocoding endpoint.
    """
    address = str(address or "").strip()
    address = re.sub(r"\s+", " ", address)
    return address


def address_fallback_queries(address):
    """
    Generate progressively broader Korean address queries.
    """
    address = normalize_korea_address_query(address)
    if not address:
        return []

    queries = [address]
    parts = address.split()

    if len(parts) >= 4:
        queries.append(" ".join(parts[:4]))
    if len(parts) >= 3:
        queries.append(" ".join(parts[:3]))
    if len(parts) >= 2:
        queries.append(" ".join(parts[:2]))

    road_tokens = []
    for token in parts:
        road_tokens.append(token)
        if token.endswith(("로", "길", "대로")):
            break
    if len(road_tokens) >= 2:
        queries.append(" ".join(road_tokens))

    seen = set()
    unique = []
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            unique.append(q)
            seen.add(q)
    return unique


def is_korea_coordinate(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except Exception:
        return False
    return (
        KOREA_BOUNDS["min_lat"] <= lat <= KOREA_BOUNDS["max_lat"]
        and KOREA_BOUNDS["min_lon"] <= lon <= KOREA_BOUNDS["max_lon"]
    )


@st.cache_data(ttl=86400)
def fetch_nominatim_candidates(address):
    """
    Search Korean addresses with OpenStreetMap Nominatim.
    This does not require an API key. It is used only for address-to-coordinate lookup.
    Current weather is still fetched from OpenWeather using the selected coordinates.
    """
    if not REQUESTS_AVAILABLE:
        return [], "requests 라이브러리가 설치되어 있지 않습니다. requirements.txt에 requests를 추가해 주세요."

    queries = address_fallback_queries(address)
    if not queries:
        return [], "주소를 입력해 주세요."

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "WattdaEnergyDiagnosis/1.0"}

    all_candidates = []
    seen = set()

    for query in queries:
        params = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 5,
            "countrycodes": "kr",
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                continue

            data = response.json()
            for item in data:
                lat = item.get("lat")
                lon = item.get("lon")
                if not is_korea_coordinate(lat, lon):
                    continue

                key = (round(float(lat), 6), round(float(lon), 6))
                if key in seen:
                    continue
                seen.add(key)

                display_name = item.get("display_name", query)
                address_data = item.get("address", {}) or {}
                city = (
                    address_data.get("city")
                    or address_data.get("town")
                    or address_data.get("county")
                    or address_data.get("state")
                    or "대한민국"
                )

                all_candidates.append({
                    "label": display_name,
                    "lat": float(lat),
                    "lon": float(lon),
                    "name": display_name,
                    "state": city,
                    "country": "KR",
                    "source": "OpenStreetMap",
                })

            if all_candidates:
                break

        except Exception:
            continue

    if not all_candidates:
        return [], "주소 검색 결과가 없습니다. 도로명 전체 또는 행정구역과 도로명을 함께 입력해 주세요. 예: 서울 강남구 테헤란로"

    return all_candidates, None


@st.cache_data(ttl=86400)
def fetch_openweather_geocoding_candidates(address, api_key):
    """
    Optional fallback geocoder using OpenWeather's direct geocoding endpoint.
    This requires OPENWEATHER_API_KEY and is used only if Nominatim returns no result.
    """
    if not REQUESTS_AVAILABLE:
        return [], "requests 라이브러리가 설치되어 있지 않습니다. requirements.txt에 requests를 추가해 주세요."

    if not api_key:
        return [], "주소 검색 결과가 없습니다. 지도에서 직접 건물 위치를 클릭해 주세요."

    queries = address_fallback_queries(address)
    if not queries:
        return [], "주소를 입력해 주세요."

    candidates = []
    seen = set()

    for query in queries:
        url = "https://api.openweathermap.org/geo/1.0/direct"
        params = {"q": f"{query},KR", "limit": 5, "appid": api_key}

        try:
            response = requests.get(url, params=params, timeout=8)
            if response.status_code != 200:
                continue

            data = response.json()
            for item in data:
                lat = item.get("lat")
                lon = item.get("lon")
                if not is_korea_coordinate(lat, lon):
                    continue

                key = (round(float(lat), 6), round(float(lon), 6))
                if key in seen:
                    continue
                seen.add(key)

                local_names = item.get("local_names", {}) or {}
                display_name = local_names.get("ko") or item.get("name") or local_names.get("en") or query
                state = item.get("state", "")
                country = item.get("country", "KR")
                label_parts = [p for p in [display_name, state, country] if p]
                label = " / ".join(label_parts)

                candidates.append({
                    "label": label,
                    "lat": float(lat),
                    "lon": float(lon),
                    "name": display_name,
                    "state": state,
                    "country": country,
                    "source": "OpenWeather",
                })

            if candidates:
                break

        except Exception:
            continue

    if not candidates:
        return [], "주소 검색 결과가 없습니다. 지도에서 직접 건물 위치를 클릭해 주세요."

    return candidates, None


@st.cache_data(ttl=86400)
def fetch_geocoding_candidates(address, api_key):
    """
    Address search coordinator.
    1. Try OpenStreetMap Nominatim first.
    2. If no result, try OpenWeather geocoding as fallback.
    """
    candidates, error = fetch_nominatim_candidates(address)
    if candidates:
        return candidates, None

    fallback_candidates, fallback_error = fetch_openweather_geocoding_candidates(address, api_key)
    if fallback_candidates:
        return fallback_candidates, None

    return [], error or fallback_error


def render_address_location_picker(info):
    """
    Address-first location picker.
    """
    st.markdown("#### 주소 기반 위치 설정")
    st.caption("건물 주소를 입력하면 해당 위치의 좌표를 찾아 실시간 기상정보에 연결합니다. 지도에서 직접 클릭해 보정할 수도 있습니다.")

    current_address = info.get("건물주소", "")
    address = st.text_input(
        "건물 주소",
        value=current_address,
        placeholder="예: 서울시 강남구 테헤란로 152",
        help="도로명 주소나 지번 주소를 입력하세요. 주소 검색 결과가 부정확하면 지도에서 직접 위치를 클릭해 보정할 수 있습니다.",
    )

    api_key = get_openweather_api_key()

    selected_city = info.get("지도기준도시", "서울")
    initial_lat, initial_lon = clamp_korea_location(
        info.get("위도", 37.5665),
        info.get("경도", 126.9780),
        selected_city,
    )

    if "selected_location_lat" not in st.session_state:
        st.session_state.selected_location_lat = initial_lat
    if "selected_location_lon" not in st.session_state:
        st.session_state.selected_location_lon = initial_lon

    selected_lat = float(st.session_state.selected_location_lat)
    selected_lon = float(st.session_state.selected_location_lon)

    if st.button("주소로 위치 찾기", use_container_width=True):
        candidates, error = fetch_geocoding_candidates(address, api_key)
        if error:
            st.warning(error)
            st.session_state.geocode_candidates = []
        else:
            st.session_state.geocode_candidates = candidates
            first = candidates[0]
            st.session_state.selected_location_lat = float(first["lat"])
            st.session_state.selected_location_lon = float(first["lon"])
            selected_lat = float(first["lat"])
            selected_lon = float(first["lon"])
            st.success("주소 후보를 찾았습니다. 필요하면 아래 지도에서 실제 건물 위치를 클릭해 보정하세요.")

    candidates = st.session_state.get("geocode_candidates", [])
    if candidates:
        labels = [c["label"] for c in candidates]
        chosen_label = st.selectbox("주소 검색 결과", labels)
        chosen = candidates[labels.index(chosen_label)]
        selected_lat = float(chosen["lat"])
        selected_lon = float(chosen["lon"])
        selected_city = chosen.get("state") or selected_city

        st.session_state.selected_location_lat = selected_lat
        st.session_state.selected_location_lon = selected_lon

        st.markdown(
            f'<span class="w-location-chip">선택 좌표: {selected_lat:.5f}, {selected_lon:.5f}</span>',
            unsafe_allow_html=True,
        )

    st.markdown("#### 지도에서 위치 확인 및 보정")
    st.caption("주소 검색 결과가 부정확하면 지도에서 실제 건물 위치를 클릭하세요.")

    if FOLIUM_AVAILABLE:
        map_lat, map_lon = clamp_korea_location(
            st.session_state.selected_location_lat,
            st.session_state.selected_location_lon,
            "서울",
        )

        m = folium.Map(
            location=[map_lat, map_lon],
            zoom_start=16,
            tiles="CartoDB positron",
            max_bounds=True,
            min_lat=KOREA_BOUNDS["min_lat"],
            max_lat=KOREA_BOUNDS["max_lat"],
            min_lon=KOREA_BOUNDS["min_lon"],
            max_lon=KOREA_BOUNDS["max_lon"],
        )

        folium.Marker(
            location=[map_lat, map_lon],
            tooltip="현재 선택 위치",
            popup=f"현재 선택 위치: {map_lat:.5f}, {map_lon:.5f}",
            icon=folium.Icon(color="blue", icon="home"),
        ).add_to(m)

        map_data = st_folium(
            m,
            height=360,
            width=None,
            returned_objects=["last_clicked"],
            key="address_location_picker_map",
        )

        if map_data and map_data.get("last_clicked"):
            clicked_lat = float(map_data["last_clicked"]["lat"])
            clicked_lon = float(map_data["last_clicked"]["lng"])
            if is_korea_coordinate(clicked_lat, clicked_lon):
                if (
                    abs(clicked_lat - float(st.session_state.selected_location_lat)) > 0.000001
                    or abs(clicked_lon - float(st.session_state.selected_location_lon)) > 0.000001
                ):
                    st.session_state.selected_location_lat = clicked_lat
                    st.session_state.selected_location_lon = clicked_lon
                    st.rerun()
            else:
                st.warning("한국 영역 안의 위치를 선택해 주세요.")
    else:
        st.warning("지도 표시를 사용하려면 requirements.txt에 folium과 streamlit-folium을 추가해야 합니다.")

    selected_lat = float(st.session_state.selected_location_lat)
    selected_lon = float(st.session_state.selected_location_lon)

    loc_cols = st.columns(2)
    loc_cols[0].metric("선택 위도", f"{selected_lat:.5f}")
    loc_cols[1].metric("선택 경도", f"{selected_lon:.5f}")

    return address, selected_city, selected_lat, selected_lon


@st.cache_data(ttl=600)
def fetch_current_weather(lat, lon, api_key):
    """
    OpenWeather Current Weather API를 사용해 현재 기상정보를 가져옵니다.
    API key가 없거나 requests가 설치되어 있지 않으면 오류 메시지를 반환합니다.
    """
    if not REQUESTS_AVAILABLE:
        return None, "requests 라이브러리가 설치되어 있지 않습니다. requirements.txt에 requests를 추가해 주세요."

    if not api_key:
        return None, "실시간 기상정보는 현재 준비 중입니다. 주소와 지도 위치는 저장되며, 기상 연동이 활성화되면 자동으로 현재 외기 조건을 불러옵니다."

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": float(lat),
        "lon": float(lon),
        "appid": api_key,
        "units": "metric",
        "lang": "kr",
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code != 200:
            return None, f"날씨 API 호출 실패: HTTP {response.status_code}"

        data = response.json()
        weather = {
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "humidity": data.get("main", {}).get("humidity"),
            "pressure": data.get("main", {}).get("pressure"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "clouds": data.get("clouds", {}).get("all"),
            "description": data.get("weather", [{}])[0].get("description"),
            "city": data.get("name"),
        }
        return weather, None
    except Exception as e:
        return None, f"날씨 데이터 처리 중 오류: {e}"


def render_current_weather_box(info):
    st.markdown("### 실시간 외기 조건")

    lat, lon = clamp_korea_location(
        info.get("위도", 37.5665),
        info.get("경도", 126.9780),
        info.get("지도기준도시", "서울"),
    )

    api_key = get_openweather_api_key()
    weather, weather_error = fetch_current_weather(lat, lon, api_key)

    if weather_error:
        st.warning(weather_error)
        st.caption("기상 연동이 활성화되기 전까지는 CSV의 실외온도 컬럼 또는 샘플 데이터 기준으로 진단이 진행됩니다.")
        return None

    try:
        w1, w2, w3, w4 = st.columns(4)
        w1.metric("현재 외기온도", f"{weather['temperature']:.1f}°C")
        w2.metric("체감온도", f"{weather['feels_like']:.1f}°C")
        w3.metric("상대습도", f"{weather['humidity']}%")
        w4.metric("풍속", f"{weather['wind_speed']:.1f} m/s")

        st.caption(
            f"날씨 상태: {weather['description']} | 관측 지역: {weather['city']} | "
            f"선택 좌표: {lat:.5f}, {lon:.5f} | 10분 캐시 적용"
        )

        if weather["temperature"] is not None:
            if float(weather["temperature"]) >= 30:
                st.warning("현재 외기온도가 높습니다. 오늘의 피크 전력은 냉방부하와 관련될 가능성이 있으므로 14~17시 사용량을 함께 확인하세요.")
            elif float(weather["temperature"]) <= 5:
                st.info("현재 외기온도가 낮습니다. 난방 또는 기저부하 관련 전력 사용 패턴을 함께 확인하는 것이 좋습니다.")
            else:
                st.info("현재 외기온도는 중간 범위입니다. 피크 전력은 냉방보다 운영시간, 조명, 설비 동시가동의 영향일 수 있습니다.")
    except Exception:
        st.warning("기상정보 일부 값이 누락되어 표시하지 못했습니다.")

    return weather


# ============================================================
# Sample data generation
# ============================================================

def make_sample_data(year=2026):
    """
    1년치 한국형 샘플 데이터
    월별 계절성, 운영시간, 휴무일 사용, 냉방 민감도, 실내온도, 습도, 점유인원을 포함
    1년 시간별 데이터는 약 8,760행이라 Streamlit에서 충분히 다룰 수 있습니다.
    """
    start = pd.Timestamp(year=year, month=1, day=1, hour=0)
    end = pd.Timestamp(year=year, month=12, day=31, hour=23)
    idx = pd.date_range(start, end, freq="h")
    rng = np.random.default_rng(73)

    rows = []
    for dt in idx:
        hour = dt.hour
        weekday = dt.weekday()
        month = dt.month

        # 학원 기본 운영: 평일 13~22, 토요일 10~18, 일요일 휴무
        if weekday in [0, 1, 2, 3, 4]:
            operating = 13 <= hour < 22
        elif weekday == 5:
            operating = 10 <= hour < 18
        else:
            operating = False

        sunday = weekday == 6

        # 서울형 계절 온도 패턴, 매우 단순화
        seasonal = 12 + 17 * np.sin((dt.dayofyear - 105) / 365 * 2 * np.pi)
        daily = 4.5 * np.sin((hour - 8) / 24 * 2 * np.pi)
        outdoor_temp = seasonal + daily + rng.normal(0, 1.2)

        # 폭염 주간 효과
        if month in [7, 8] and dt.day in [5, 6, 7, 8, 18, 19, 20, 21]:
            outdoor_temp += 2.2

        base_load = 13.0

        # 계절별 냉난방 기본 부하
        if month in [6, 7, 8, 9]:
            seasonal_load = max(outdoor_temp - 25, 0) * 4.2
        elif month in [12, 1, 2]:
            seasonal_load = max(4 - outdoor_temp, 0) * 1.6
        else:
            seasonal_load = 2.5

        occupancy = 0
        if operating:
            if weekday == 5:
                occ_base = 45 + 35 * np.sin(max(hour - 9, 0) / 8 * np.pi)
            else:
                occ_base = 35 + 55 * np.sin(max(hour - 12, 0) / 9 * np.pi)
            occupancy = max(0, int(occ_base + rng.normal(0, 8)))
            occupancy = min(occupancy, 120)

            base_load += 30
            base_load += seasonal_load
            if 15 <= hour <= 21 and weekday < 5:
                base_load += 8.0
        else:
            occupancy = max(0, int(rng.normal(3, 2)))
            base_load += seasonal_load * 0.30

        # 오후 피크
        if operating and month in [7, 8] and 14 <= hour <= 17:
            base_load += 8.0

        # 휴무일 낭비
        if sunday:
            base_load += 7.0
            if 12 <= hour <= 20:
                base_load += 5.5

        # 야간 기저부하
        if hour >= 22 or hour < 6:
            base_load += 5.0

        electricity = max(6.0, base_load + rng.normal(0, 2.0))

        # 실내온도, 대략적 시뮬레이션
        if operating:
            if month in [6, 7, 8, 9]:
                indoor_temp = 24.7 + max(outdoor_temp - 30, 0) * 0.18 + rng.normal(0, 0.5)
            elif month in [12, 1, 2]:
                indoor_temp = 21.5 - max(2 - outdoor_temp, 0) * 0.04 + rng.normal(0, 0.5)
            else:
                indoor_temp = 23.0 + rng.normal(0, 0.7)
        else:
            indoor_temp = 24.0 + max(outdoor_temp - 28, 0) * 0.28 - max(3 - outdoor_temp, 0) * 0.06 + rng.normal(0, 0.7)

        rh = 55 + rng.normal(0, 7)
        if month in [7, 8]:
            rh += 6
        if operating:
            rh -= 3
        rh = min(max(rh, 35), 80)

        rows.append({
            COL_DT: dt,
            COL_KWH: round(electricity, 2),
            COL_OUT: round(outdoor_temp, 1),
            COL_IN: round(indoor_temp, 1),
            COL_RH: round(rh, 1),
            COL_OCC: int(occupancy),
        })

    return pd.DataFrame(rows)


# ============================================================
# Data prep and analysis
# ============================================================

def prepare_data(df):
    df = df.copy()
    df[COL_DT] = pd.to_datetime(df[COL_DT])
    df = df.sort_values(COL_DT)
    df["시간"] = df[COL_DT].dt.hour
    df["날짜"] = df[COL_DT].dt.date
    df["요일번호"] = df[COL_DT].dt.weekday
    df["주말여부"] = df["요일번호"].isin([5, 6])
    return df


def analyze(df, info):
    df = prepare_data(df)

    day_map = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}
    reverse_day_map = {v: k for k, v in day_map.items()}

    # 요일별 운영시간을 우선 적용합니다.
    # 이전 버전 정보가 들어오면 기존의 운영요일, 운영시작, 운영종료 방식으로도 작동합니다.
    schedule = info.get("운영스케줄")
    if schedule:
        def is_operating_row(row):
            day_name = reverse_day_map.get(int(row["요일번호"]), "")
            day_schedule = schedule.get(day_name, {})
            if not day_schedule.get("운영", False):
                return False

            start_t = day_schedule.get("시작", time(9, 0))
            end_t = day_schedule.get("종료", time(18, 0))
            h = int(row["시간"])
            s = start_t.hour
            e = end_t.hour

            if s < e:
                return s <= h < e
            return h >= s or h < e

        df["운영시간여부"] = df.apply(is_operating_row, axis=1)
    else:
        operating_days = [day_map[d] for d in info["운영요일"] if d in day_map]
        start_hour = info["운영시작"].hour
        end_hour = info["운영종료"].hour

        if start_hour < end_hour:
            df["운영시간여부"] = df["요일번호"].isin(operating_days) & (df["시간"] >= start_hour) & (df["시간"] < end_hour)
        else:
            df["운영시간여부"] = df["요일번호"].isin(operating_days) & ((df["시간"] >= start_hour) | (df["시간"] < end_hour))

    df["야간여부"] = (df["시간"] >= 22) | (df["시간"] < 6)

    monthly_bill = float(info["월전기요금"])
    monthly_kwh = float(info["월전력사용량"])
    unit_price = safe_div(monthly_bill, monthly_kwh, 0)

    total_kwh = float(df[COL_KWH].sum())
    avg_hourly = float(df[COL_KWH].mean())
    max_hourly = float(df[COL_KWH].max())

    operating_avg = float(df.loc[df["운영시간여부"], COL_KWH].mean())
    non_operating_avg = float(df.loc[~df["운영시간여부"], COL_KWH].mean())
    night_avg = float(df.loc[df["야간여부"], COL_KWH].mean())
    night_ratio = safe_div(night_avg, operating_avg) * 100

    daily = df.groupby("날짜", as_index=False)[COL_KWH].sum()
    daily_avg = float(daily[COL_KWH].mean())
    abnormal_days = daily[daily[COL_KWH] > daily_avg * 1.20]

    weekday_daily = float(df.loc[~df["주말여부"]].groupby("날짜")[COL_KWH].sum().mean())
    weekend_daily = float(df.loc[df["주말여부"]].groupby("날짜")[COL_KWH].sum().mean())
    weekend_ratio = safe_div(weekend_daily, weekday_daily) * 100

    peak = df.loc[df[COL_KWH].idxmax()]
    top_peaks = df.sort_values(COL_KWH, ascending=False).head(5)

    hourly_profile = df.groupby("시간", as_index=False)[COL_KWH].mean().rename(columns={COL_KWH: "평균전력사용량(kWh)"})

    cooling_sensitivity = None
    cooling_r2 = None
    if COL_OUT in df.columns:
        tmp = df.dropna(subset=[COL_OUT, COL_KWH])
        if len(tmp) > 12 and tmp[COL_OUT].nunique() > 3:
            x = tmp[COL_OUT].to_numpy()
            y = tmp[COL_KWH].to_numpy()
            slope, intercept = np.polyfit(x, y, 1)
            pred = slope * x + intercept
            ss_res = ((y - pred) ** 2).sum()
            ss_tot = ((y - y.mean()) ** 2).sum()
            cooling_sensitivity = float(slope)
            cooling_r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0

    indoor_hot_hours = 0
    indoor_avg = None
    if COL_IN in df.columns:
        indoor_df = df.loc[df["운영시간여부"]].dropna(subset=[COL_IN])
        if len(indoor_df) > 0:
            indoor_avg = float(indoor_df[COL_IN].mean())
            indoor_hot_hours = int((indoor_df[COL_IN] >= 27.5).sum())

    humidity_high_hours = 0
    humidity_avg = None
    if COL_RH in df.columns:
        hum_df = df.loc[df["운영시간여부"]].dropna(subset=[COL_RH])
        if len(hum_df) > 0:
            humidity_avg = float(hum_df[COL_RH].mean())
            humidity_high_hours = int((hum_df[COL_RH] >= 65).sum())

    low_occupancy_ratio = None
    if COL_OCC in df.columns:
        occ_df = df.loc[df["운영시간여부"]].dropna(subset=[COL_OCC])
        if len(occ_df) > 0 and occ_df[COL_OCC].max() > 0:
            occ_peak = float(occ_df[COL_OCC].max())
            threshold = occ_peak * 0.2
            low_occ = occ_df[occ_df[COL_OCC] <= threshold]
            if len(low_occ) > 0:
                low_occ_avg = float(low_occ[COL_KWH].mean())
                low_occupancy_ratio = safe_div(low_occ_avg, operating_avg) * 100

    target_night_avg = operating_avg * 0.35
    avoidable_night_kwh = max(0, night_avg - target_night_avg) * len(df[df["야간여부"]])
    night_saving = avoidable_night_kwh * unit_price

    target_weekend_daily = weekday_daily * 0.40
    weekend_days = df.loc[df["주말여부"], "날짜"].nunique()
    avoidable_weekend_kwh = max(0, weekend_daily - target_weekend_daily) * weekend_days
    weekend_saving = avoidable_weekend_kwh * unit_price

    if cooling_sensitivity is not None and cooling_sensitivity > 0 and COL_OUT in df.columns:
        cooling_related_kwh = float(np.maximum(df[COL_OUT] - 26, 0).sum() * cooling_sensitivity)
        cooling_saving_low = cooling_related_kwh * unit_price * 0.035
        cooling_saving_high = cooling_related_kwh * unit_price * 0.08
    else:
        cooling_saving_low = monthly_bill * 0.02
        cooling_saving_high = monthly_bill * 0.05

    comfort_saving = 0
    if indoor_hot_hours > 0:
        comfort_saving += monthly_bill * 0.01
    if low_occupancy_ratio is not None and low_occupancy_ratio >= 70:
        comfort_saving += monthly_bill * 0.01

    total_saving_low = night_saving + weekend_saving + cooling_saving_low + comfort_saving
    total_saving_high = night_saving + weekend_saving + cooling_saving_high + comfort_saving

    score = 100
    if night_ratio >= 55:
        score -= 24
    elif night_ratio >= 45:
        score -= 16
    elif night_ratio >= 35:
        score -= 8

    if weekend_ratio >= 60:
        score -= 22
    elif weekend_ratio >= 50:
        score -= 15
    elif weekend_ratio >= 40:
        score -= 8

    if cooling_sensitivity is not None:
        if cooling_sensitivity >= 5:
            score -= 16
        elif cooling_sensitivity >= 3:
            score -= 9

    if indoor_hot_hours >= 20:
        score -= 8
    elif indoor_hot_hours >= 8:
        score -= 4

    if low_occupancy_ratio is not None:
        if low_occupancy_ratio >= 75:
            score -= 8
        elif low_occupancy_ratio >= 65:
            score -= 4

    if len(abnormal_days) >= 5:
        score -= 10
    elif len(abnormal_days) >= 3:
        score -= 5

    score = max(0, min(100, int(round(score))))

    if score >= 80:
        grade, risk = "A", "양호"
    elif score >= 65:
        grade, risk = "B", "주의"
    elif score >= 50:
        grade, risk = "C", "개선 필요"
    else:
        grade, risk = "D", "우선 개선 필요"

    return {
        "df": df,
        "daily": daily,
        "abnormal_days": abnormal_days,
        "hourly_profile": hourly_profile,
        "unit_price": unit_price,
        "total_kwh": total_kwh,
        "avg_hourly": avg_hourly,
        "max_hourly": max_hourly,
        "operating_avg": operating_avg,
        "non_operating_avg": non_operating_avg,
        "night_avg": night_avg,
        "night_ratio": night_ratio,
        "weekday_daily": weekday_daily,
        "weekend_daily": weekend_daily,
        "weekend_ratio": weekend_ratio,
        "peak": peak,
        "top_peaks": top_peaks,
        "cooling_sensitivity": cooling_sensitivity,
        "cooling_r2": cooling_r2,
        "indoor_avg": indoor_avg,
        "indoor_hot_hours": indoor_hot_hours,
        "humidity_avg": humidity_avg,
        "humidity_high_hours": humidity_high_hours,
        "low_occupancy_ratio": low_occupancy_ratio,
        "avoidable_night_kwh": avoidable_night_kwh,
        "night_saving": night_saving,
        "avoidable_weekend_kwh": avoidable_weekend_kwh,
        "weekend_saving": weekend_saving,
        "cooling_saving_low": cooling_saving_low,
        "cooling_saving_high": cooling_saving_high,
        "comfort_saving": comfort_saving,
        "total_saving_low": total_saving_low,
        "total_saving_high": total_saving_high,
        "score": score,
        "grade": grade,
        "risk": risk,
    }


# ============================================================
# Diagnosis helpers
# ============================================================

def core_issues(result):
    issues = []
    if result["night_ratio"] >= 45:
        issues.append("야간 기저부하 높음")
    elif result["night_ratio"] >= 35:
        issues.append("야간 기저부하 주의")

    if result["weekend_ratio"] >= 50:
        issues.append("휴무일 사용량 높음")
    elif result["weekend_ratio"] >= 40:
        issues.append("휴무일 사용량 주의")

    if result["cooling_sensitivity"] is not None:
        if result["cooling_sensitivity"] >= 5:
            issues.append("냉방 민감도 높음")
        elif result["cooling_sensitivity"] >= 3:
            issues.append("냉방 민감도 주의")

    if result["indoor_hot_hours"] >= 8:
        issues.append("실내 온도 관리 필요")

    if result["low_occupancy_ratio"] is not None and result["low_occupancy_ratio"] >= 70:
        issues.append("저점유 시간 전력 사용 높음")

    if result["humidity_high_hours"] >= 8:
        issues.append("실내 습도 관리 필요")

    return issues or ["큰 이상 패턴 없음"]


def diagnosis_blocks(info, result):
    blocks = []

    if result["night_ratio"] >= 35:
        blocks.append({
            "제목": "야간 기저부하",
            "문제": f"운영 종료 후에도 야간 평균 전력 사용량이 {result['night_avg']:.1f} kWh/h이며, 운영시간 평균 사용량의 {result['night_ratio']:.1f}% 수준입니다.",
            "원인": "간판, 공용부 조명, 환기팬, 시스템에어컨 잔류 운전, 대기전력 장비가 원인일 수 있습니다.",
            "비용": f"현재 데이터 기준 약 {krw(result['night_saving'])}/월 수준의 절감 가능성이 추정됩니다.",
            "조치": "22:30 이후 현장 점검을 1회 실시하고 켜져 있는 설비를 기록한 뒤 종료 체크리스트를 운영하세요.",
            "확인": f"다음 달에는 야간 평균 사용량이 {result['night_avg']:.1f} kWh/h에서 {max(result['operating_avg'] * 0.35, 0):.1f} kWh/h 수준으로 낮아졌는지 확인합니다.",
        })

    if result["weekend_ratio"] >= 40:
        blocks.append({
            "제목": "휴무일 전력 사용",
            "문제": f"주말 평균 전력 사용량이 평일 평균의 {result['weekend_ratio']:.1f}% 수준입니다.",
            "원인": "휴무일에도 조명, 냉방, 환기, 간판 또는 공용부 설비가 계속 작동하고 있을 수 있습니다.",
            "비용": f"현재 데이터 기준 약 {krw(result['weekend_saving'])}/월 수준의 절감 가능성이 추정됩니다.",
            "조치": "휴무일 오전과 오후에 설비 가동 상태를 확인하고 운영일과 휴무일 스케줄을 분리하세요.",
            "확인": f"다음 달에는 주말 사용률이 {result['weekend_ratio']:.1f}%에서 40% 이하로 낮아졌는지 확인합니다.",
        })

    if result["cooling_sensitivity"] is not None and result["cooling_sensitivity"] >= 3:
        blocks.append({
            "제목": "냉방 민감도",
            "문제": f"실외온도 1°C 상승 시 전력 사용량이 약 {result['cooling_sensitivity']:.1f} kWh 증가하는 것으로 추정됩니다.",
            "원인": "오후 시간대 시스템에어컨 동시 가동, 사용하지 않는 공간 냉방, 낮은 설정온도, 스케줄 불일치가 원인일 수 있습니다.",
            "비용": f"냉방 스케줄 조정으로 약 {krw(result['cooling_saving_low'])}부터 {krw(result['cooling_saving_high'])}/월의 절감 가능성이 추정됩니다.",
            "조치": "오후 피크 시간대에 사용하지 않는 공간 냉방을 제한하고 설정온도와 예냉 시간을 조정하세요.",
            "확인": "다음 달에는 14시부터 17시 사이 피크 사용량과 실내 온도 변화를 같이 확인합니다.",
        })

    if result["indoor_avg"] is not None:
        blocks.append({
            "제목": "실내 온도",
            "문제": f"운영시간 평균 실내온도는 {result['indoor_avg']:.1f}°C이며, 27.5°C 이상 시간은 {result['indoor_hot_hours']}시간입니다.",
            "원인": "냉방 용량 분배, 설정온도, 외기 부하, 일사 유입, 공간별 사용 밀도 차이가 영향을 줄 수 있습니다.",
            "비용": "실내온도는 쾌적성뿐 아니라 냉방 운전 효율에도 영향을 줍니다. 과열과 과냉을 함께 줄이는 것이 중요합니다.",
            "조치": "더운 시간대와 공간을 먼저 확인하고, 냉방이 필요한 공간과 그렇지 않은 공간의 운전을 구분하세요.",
            "확인": "다음 달에는 27.5°C 이상 시간과 민원 발생 시간대가 줄었는지 확인합니다.",
        })

    if result["low_occupancy_ratio"] is not None:
        blocks.append({
            "제목": "점유 대비 전력 사용",
            "문제": f"저점유 시간 전력 사용량은 운영시간 평균의 {result['low_occupancy_ratio']:.1f}% 수준입니다.",
            "원인": "부분 점유 상황에서도 조명, 냉방, 환기, 공용부 설비가 전체 운전 상태로 유지되고 있을 수 있습니다.",
            "비용": "점유도에 따라 부분 운전이 가능하면 추가 절감 여지가 생길 수 있습니다.",
            "조치": "학생 수나 방문자 수가 적은 시간대에 공간별 부분 운전을 적용할 수 있는지 검토하세요.",
            "확인": "다음 달에는 저점유 시간 평균 전력 사용량이 운영시간 평균 대비 낮아졌는지 확인합니다.",
        })

    if result["humidity_avg"] is not None:
        blocks.append({
            "제목": "실내 습도",
            "문제": f"운영시간 평균 상대습도는 {result['humidity_avg']:.1f}%이며, 65% 이상 시간은 {result['humidity_high_hours']}시간입니다.",
            "원인": "외기 유입, 환기량, 냉방 제어, 공간 밀도가 실내 습도에 영향을 줄 수 있습니다.",
            "비용": "높은 습도는 체감 불쾌감을 높여 더 낮은 설정온도를 요구하게 만들 수 있습니다.",
            "조치": "습도가 높은 시간대에 냉방, 환기, 외기 유입 상태를 함께 확인하세요.",
            "확인": "다음 달에는 65% 이상 시간대가 줄었는지 확인합니다.",
        })

    peak = result["peak"]
    blocks.append({
        "제목": "피크 시간",
        "문제": f"최대 전력 사용은 {peak[COL_DT].strftime('%m월 %d일 %H시')}에 발생했으며 사용량은 {peak[COL_KWH]:.1f} kWh입니다.",
        "원인": "냉방, 조명, 설비 운전이 특정 시간에 동시에 집중되었을 가능성이 있습니다.",
        "비용": "피크 발생 원인을 줄이면 전기요금 구조에 따라 비용 완화에 도움이 될 수 있습니다.",
        "조치": "피크 Top 5 시간대에 실제 설비 운전 상태와 공간 사용 상황을 확인하세요.",
        "확인": "다음 달에도 동일 시간대에 피크가 반복되는지 확인합니다.",
    })

    return blocks


def recommendations(result):
    rows = []
    if result["night_ratio"] >= 45:
        rows.append(["1", "영업 종료 후 조명, 간판, 콘센트, 환기팬, 시스템에어컨 종료 상태 점검", "높음", "낮음"])
    elif result["night_ratio"] >= 35:
        rows.append(["1", "야간 대기전력과 공용부 전력 사용 점검", "중간", "낮음"])

    if result["weekend_ratio"] >= 40:
        rows.append([str(len(rows) + 1), "휴무일 냉방, 조명, 간판, 환기 스케줄 분리", "중간에서 높음", "낮음"])

    if result["cooling_sensitivity"] is not None and result["cooling_sensitivity"] >= 3:
        rows.append([str(len(rows) + 1), "오후 피크 시간대 냉방 설정온도와 공간별 운전 스케줄 조정", "중간", "중간"])

    if result["low_occupancy_ratio"] is not None:
        rows.append([str(len(rows) + 1), "저점유 시간대 부분 운전 또는 구역별 운전 검토", "중간", "중간"])

    rows.append([str(len(rows) + 1), "피크 Top 5 시간대의 실제 설비 운전 상태 확인", "중간", "낮음"])
    return pd.DataFrame(rows, columns=["우선순위", "개선 조치", "예상 효과", "난이도"])


# ============================================================
# Visualization helpers
# ============================================================

def build_cuboid(origin, size):
    x, y, z = origin
    dx, dy, dz = size
    return [
        [(x, y, z), (x+dx, y, z), (x+dx, y+dy, z), (x, y+dy, z)],
        [(x, y, z+dz), (x+dx, y, z+dz), (x+dx, y+dy, z+dz), (x, y+dy, z+dz)],
        [(x, y, z), (x+dx, y, z), (x+dx, y, z+dz), (x, y, z+dz)],
        [(x, y+dy, z), (x+dx, y+dy, z), (x+dx, y+dy, z+dz), (x, y+dy, z+dz)],
        [(x, y, z), (x, y+dy, z), (x, y+dy, z+dz), (x, y, z+dz)],
        [(x+dx, y, z), (x+dx, y+dy, z), (x+dx, y+dy, z+dz), (x+dx, y, z+dz)],
    ]


def draw_building_preview_3d(info):
    floors = max(1, int(info["층수"]))
    width = max(2.5, min(8.0, info["연면적"] / max(floors, 1) / 120))
    depth = max(2.0, min(6.5, width * 0.65))
    height = floors

    fig = plt.figure(figsize=(6, 5.8))
    ax = fig.add_subplot(111, projection="3d")

    faces = build_cuboid((0, 0, 0), (width, depth, height))
    poly = Poly3DCollection(faces, linewidths=0.8, edgecolors="black", alpha=0.45)
    ax.add_collection3d(poly)

    for f in range(1, floors):
        ax.plot([0, width], [0, 0], [f, f])
        ax.plot([0, width], [depth, depth], [f, f])
        ax.plot([0, 0], [0, depth], [f, f])
        ax.plot([width, width], [0, depth], [f, f])

    win_cols = int(np.clip(round(width), 3, 7))
    for floor in range(floors):
        z0 = floor + 0.25
        for c in range(win_cols):
            x0 = 0.35 + c * (width - 0.7) / win_cols
            ax.plot([x0, x0+0.32], [depth+0.001, depth+0.001], [z0, z0], linewidth=1)
            ax.plot([x0, x0+0.32], [depth+0.001, depth+0.001], [z0+0.35, z0+0.35], linewidth=1)
            ax.plot([x0, x0], [depth+0.001, depth+0.001], [z0, z0+0.35], linewidth=1)
            ax.plot([x0+0.32, x0+0.32], [depth+0.001, depth+0.001], [z0, z0+0.35], linewidth=1)

    ax.set_xlim(0, width + 1.0)
    ax.set_ylim(0, depth + 1.0)
    ax.set_zlim(0, height + 1.2)
    ax.view_init(elev=22, azim=-58)
    ax.set_axis_off()
    ax.set_title(f"{info['건물명']}\n{info['건물용도']} | {info['지역']}\n연면적 {info['연면적']:,}㎡ | {floors}층", pad=12)
    return fig


def fig_to_png_bytes(fig):
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()



def get_today_df_for_display(df):
    """한국 기준 오늘 날짜 데이터를 반환하고, 없으면 데이터의 가장 최근 날짜를 반환합니다."""
    today_kst = pd.Timestamp.now(tz="Asia/Seoul").date()
    today_df = df[df[COL_DT].dt.date == today_kst].copy()
    display_date = today_kst
    used_fallback = False

    if today_df.empty:
        display_date = df[COL_DT].dt.date.max()
        today_df = df[df[COL_DT].dt.date == display_date].copy()
        used_fallback = True

    today_df = today_df.sort_values(COL_DT)
    today_df["시각"] = today_df[COL_DT].dt.hour
    return today_df, display_date, used_fallback


def make_today_power_graph(result):
    df = result["df"]
    today_df, display_date, _ = get_today_df_for_display(df)

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.plot(today_df["시각"], today_df[COL_KWH], marker="o", linewidth=1.8)
    ax.set_title(f"오늘 하루 전력 사용량 | {display_date}")
    ax.set_xlabel("시각")
    ax.set_ylabel("전력사용량(kWh)")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, alpha=0.25)
    return fig


def make_monthly_power_graph(result):
    df = result["df"].copy()
    df["월"] = df[COL_DT].dt.month
    monthly_summary = df.groupby("월", as_index=False)[COL_KWH].sum()

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.bar(monthly_summary["월"], monthly_summary[COL_KWH])
    ax.set_title("월별 전력 사용량")
    ax.set_xlabel("월")
    ax.set_ylabel("전력사용량(kWh)")
    ax.set_xticks(range(1, 13))
    ax.grid(axis="y", alpha=0.25)
    return fig


def make_today_temperature_graph(result):
    df = result["df"]
    today_df, display_date, _ = get_today_df_for_display(df)

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    if COL_IN in today_df.columns:
        ax.plot(today_df["시각"], today_df[COL_IN], marker="o", linewidth=1.8, label="실내온도")
    if COL_OUT in today_df.columns:
        ax.plot(today_df["시각"], today_df[COL_OUT], marker="o", linewidth=1.8, color="red", label="실외온도")
    ax.set_title(f"오늘 하루 실내외 온도 추이 | {display_date}")
    ax.set_xlabel("시각")
    ax.set_ylabel("온도(°C)")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, alpha=0.25)
    ax.legend()
    return fig


def make_monthly_temperature_graph(result):
    df = result["df"].copy()
    df["월"] = df[COL_DT].dt.month
    monthly = df.groupby("월", as_index=False).agg({
        COL_IN: "mean" if COL_IN in df.columns else "size",
        COL_OUT: "mean" if COL_OUT in df.columns else "size",
    })

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    x = np.arange(1, 13)
    width = 0.36

    if COL_IN in monthly.columns:
        ax.bar(monthly["월"] - width / 2, monthly[COL_IN], width=width, label="실내온도")
    if COL_OUT in monthly.columns:
        ax.bar(monthly["월"] + width / 2, monthly[COL_OUT], width=width, label="실외온도", color="red")

    ax.set_title("월별 평균 실내외 온도")
    ax.set_xlabel("월")
    ax.set_ylabel("평균온도(°C)")
    ax.set_xticks(range(1, 13))
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    return fig


def generate_report_graphs(result):
    """
    리포트에는 오늘 하루 전력 사용량과 월별 전력 사용량 그래프만 포함합니다.
    """
    graphs = []

    fig1 = make_today_power_graph(result)
    graphs.append({"title": "오늘 하루 전력 사용량", "bytes": fig_to_png_bytes(fig1)})

    fig2 = make_monthly_power_graph(result)
    graphs.append({"title": "월별 전력 사용량", "bytes": fig_to_png_bytes(fig2)})

    return graphs


def build_report_body(info, result):
    issues = ", ".join(core_issues(result))
    peak = result["peak"]
    text = f"""# Wattda 전기요금 진단 리포트

## 1. 요약
건물명: {info['건물명']}
건물 주소: {info.get('건물주소', '미입력')}
선택 좌표: {float(info.get('위도', 37.5665)):.5f}, {float(info.get('경도', 126.9780)):.5f}
진단 점수: {result['score']}/100
진단 등급: {result['grade']}등급, {result['risk']}
핵심 문제: {issues}
예상 월 절감액: {krw(result['total_saving_low'])}부터 {krw(result['total_saving_high'])}
예상 연간 절감액: {krw(result['total_saving_low'] * 12)}부터 {krw(result['total_saving_high'] * 12)}

## 2. 핵심 수치
월 전기요금: {krw(info['월전기요금'])}
월 전력사용량: {kwh(info['월전력사용량'])}
평균 단가: {result['unit_price']:.1f}원/kWh
야간 사용 비율: {pct(result['night_ratio'])}
주말 사용 비율: {pct(result['weekend_ratio'])}
최대 시간 사용량: {kwh(result['max_hourly'])}
피크 발생 시점: {peak[COL_DT].strftime('%m월 %d일 %H시')}

## 3. 전문 진단 지표
전력 EUI: {professional_kpis(info, result)['electric_eui']:.1f} kWh/㎡·년
부하율: {professional_kpis(info, result)['load_factor']:.1f}%
기저부하 비중: {professional_kpis(info, result)['baseload_ratio']:.1f}%
계약전력 사용률: {professional_kpis(info, result)['contract_utilization']:.1f}%
반복 피크 시간대: {professional_kpis(info, result)['repeated_peak_hour']}시
데이터 품질 점수: {data_quality_summary(result['df'])['score']}/100
진단 신뢰도: {confidence_from_quality(result, data_quality_summary(result['df']))}

## 4. 절감액 해석과 검증 방식
현재 표시되는 절감액은 시간별 전력 데이터, 운영시간, 주말 사용, 냉방 민감도에 기반한 예비 추정치입니다.
실제 절감 성과는 개선 전후의 전력 데이터를 동일 조건에서 비교해 검증해야 합니다.
권장 검증 방식: 건물 전체 전력 기반 사후 검증. 최소 1개월 이상, 가능하면 동일 계절의 개선 전후 데이터를 비교하는 것을 권장합니다.

## 5. 상세 진단 요약
"""
    for block in diagnosis_blocks(info, result)[:5]:
        text += f"""
### {block['제목']}
문제: {block['문제']}
원인 추정: {block['원인']}
비용 영향: {block['비용']}
바로 할 조치: {block['조치']}
다음 달 확인 방법: {block['확인']}
"""

    rec_df = recommendations(result)
    text += "\n## 6. 우선 개선 조치\n"
    for _, row in rec_df.iterrows():
        text += f"{row['우선순위']}. {row['개선 조치']} | 예상 효과: {row['예상 효과']} | 난이도: {row['난이도']}\n"

    text += """

## 7. 간략 그래프 요약
아래 그래프는 오늘 하루 전력 사용량과 월별 전력 사용량을 보여줍니다. 하루 중 사용 패턴과 연간 월별 사용 흐름을 함께 확인하기 위한 요약 그래프입니다.
"""
    return text


def report_reference_text():
    return """
## 8. 참고
이 리포트는 시간별 전력 데이터와 건물 기본정보를 바탕으로 생성된 운영 진단 결과입니다. 실제 절감액은 운영 방식, 요금제, 계절 조건에 따라 달라질 수 있습니다.
"""


def markdown_report(info, result):
    base = build_report_body(info, result)
    graphs = generate_report_graphs(result)
    md = base + "\n"
    for graph in graphs:
        b64 = base64.b64encode(graph["bytes"]).decode("utf-8")
        md += f"\n### {graph['title']}\n"
        md += f'<img src="data:image/png;base64,{b64}" alt="{graph["title"]}" width="700">\n'
    md += "\n" + report_reference_text()
    return md


def html_report(info, result):
    body = build_report_body(info, result)
    lines = body.split("\n")
    html_parts = []
    for line in lines:
        t = html.escape(line.strip())
        if not t:
            html_parts.append("")
        elif t.startswith("# "):
            html_parts.append(f"<h1>{t[2:]}</h1>")
        elif t.startswith("## "):
            html_parts.append(f"<h2>{t[3:]}</h2>")
        elif t.startswith("### "):
            html_parts.append(f"<h3>{t[4:]}</h3>")
        else:
            html_parts.append(f"<p>{t}</p>")

    for graph in generate_report_graphs(result):
        b64 = base64.b64encode(graph["bytes"]).decode("utf-8")
        html_parts.append(f"<h3>{graph['title']}</h3>")
        html_parts.append(f'<img src="data:image/png;base64,{b64}" alt="{graph["title"]}" style="max-width:100%; border:1px solid #ddd; border-radius:8px;">')

    for line in report_reference_text().split("\n"):
        t = html.escape(line.strip())
        if not t:
            continue
        elif t.startswith("## "):
            html_parts.append(f"<h2>{t[3:]}</h2>")
        else:
            html_parts.append(f"<p>{t}</p>")

    return f"""<!doctype html>
<html lang=\"ko\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>Wattda Report</title>
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Malgun Gothic', Arial, sans-serif;
  max-width: 920px;
  margin: 34px auto;
  padding: 0 18px 36px;
  color: #111827;
  line-height: 1.72;
}}
h1 {{ font-size: 30px; border-bottom: 3px solid #111827; padding-bottom: 12px; }}
h2 {{ font-size: 21px; margin-top: 30px; color: #1F2937; }}
h3 {{ font-size: 17px; margin-top: 22px; color: #374151; }}
p {{ margin: 8px 0; }}
img {{ margin: 8px 0 18px 0; }}
</style>
</head>
<body>
{''.join(html_parts)}
</body>
</html>"""


def pdf_bytes(info, result):
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=34, leftMargin=34, topMargin=34, bottomMargin=34)

    font_name = "Helvetica"
    if FONT_PATH:
        try:
            pdfmetrics.registerFont(TTFont("KRFont", FONT_PATH))
            font_name = "KRFont"
        except Exception:
            pass

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle("w_title", parent=styles["Title"], fontName=font_name, fontSize=16, leading=22, spaceAfter=12)
    style_h2 = ParagraphStyle("w_h2", parent=styles["Heading2"], fontName=font_name, fontSize=12, leading=16, spaceBefore=10, spaceAfter=6)
    style_h3 = ParagraphStyle("w_h3", parent=styles["Heading3"], fontName=font_name, fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4)
    style_body = ParagraphStyle("w_body", parent=styles["BodyText"], fontName=font_name, fontSize=8.8, leading=13, spaceAfter=4)

    story = []
    for line in build_report_body(info, result).split("\n"):
        t = line.strip()
        if not t:
            story.append(Spacer(1, 3))
            continue
        t = html.escape(t)
        if t.startswith("# "):
            story.append(Paragraph(t[2:], style_title))
        elif t.startswith("## "):
            story.append(Paragraph(t[3:], style_h2))
        elif t.startswith("### "):
            story.append(Paragraph(t[4:], style_h3))
        else:
            story.append(Paragraph(t, style_body))

    for graph in generate_report_graphs(result):
        story.append(Paragraph(graph["title"], style_h3))
        story.append(RLImage(io.BytesIO(graph["bytes"]), width=500, height=205))
        story.append(Spacer(1, 6))

    for line in report_reference_text().split("\n"):
        t = line.strip()
        if not t:
            continue
        t = html.escape(t)
        if t.startswith("## "):
            story.append(Paragraph(t[3:], style_h2))
        else:
            story.append(Paragraph(t, style_body))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# Session state
# ============================================================

default_info = {
    "건물명": "Wattda 샘플 학원 A",
    "건물용도": "학원",
    "지역": "서울 강남구",
    "건물주소": "서울시 강남구",
    "지도기준도시": "서울",
    "위도": 37.5665,
    "경도": 126.9780,
    "연면적": 1200,
    "층수": 5,
    "운영요일": ["월", "화", "수", "목", "금", "토"],
    "운영시작": time(13, 0),
    "운영종료": time(22, 0),
    "운영스케줄": {
        "월": {"운영": True, "시작": time(13, 0), "종료": time(22, 0)},
        "화": {"운영": True, "시작": time(13, 0), "종료": time(22, 0)},
        "수": {"운영": True, "시작": time(13, 0), "종료": time(22, 0)},
        "목": {"운영": True, "시작": time(13, 0), "종료": time(22, 0)},
        "금": {"운영": True, "시작": time(13, 0), "종료": time(22, 0)},
        "토": {"운영": True, "시작": time(10, 0), "종료": time(18, 0)},
        "일": {"운영": False, "시작": time(10, 0), "종료": time(18, 0)},
    },
    "월전기요금": 3800000,
    "월전력사용량": 18500,
    "계약전력": 80,
    "요금종별": "일반용 전력 갑",
    "냉방방식": "시스템에어컨",
}

if "info" not in st.session_state:
    st.session_state.info = default_info.copy()
if "data" not in st.session_state:
    st.session_state.data = make_sample_data()
if "result" not in st.session_state:
    st.session_state.result = analyze(st.session_state.data, st.session_state.info)


def refresh_analysis():
    st.session_state.result = analyze(st.session_state.data, st.session_state.info)



# ============================================================
# Clean UI helpers for v0.4
# ============================================================

def render_top_header():
    st.markdown(
        """
        <div class="w-app-header">
            <div>
                <div class="w-app-kicker">Wattda Diagnostic Tool</div>
                <h1>건물 전기요금 진단</h1>
                <p>건물 주소, 운영정보, 전력 데이터를 입력하면 실시간 외기 조건과 함께 전기요금 낭비 요인, 피크 시간대, 예상 절감액, 개선 조치를 확인할 수 있습니다.</p>
            </div>
            <div class="w-app-status">제작자: 소정호</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_bar(active_step=1):
    steps = [
        (1, "건물 정보"),
        (2, "데이터 입력"),
        (3, "진단 결과"),
    ]
    html_steps = ""
    for num, label in steps:
        cls = "w-step-active" if num == active_step else "w-step"
        html_steps += f'<div class="{cls}"><span>{num}</span>{label}</div>'
    st.markdown(f'<div class="w-stepbar">{html_steps}</div>', unsafe_allow_html=True)


def render_quick_start_cards():
    st.markdown("### 시작하기")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            """
            <div class="w-action-card">
                <div class="w-action-title">빠른 체험</div>
                <div class="w-action-desc">샘플 데이터로 바로 진단 결과를 확인합니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("샘플 데이터로 바로 체험하기", type="primary", use_container_width=True):
            st.session_state.data = make_sample_data()
            refresh_analysis()
            st.session_state.current_step = 3
            st.rerun()

    with c2:
        st.markdown(
            """
            <div class="w-action-card">
                <div class="w-action-title">내 데이터로 진단</div>
                <div class="w-action-desc">건물 정보와 CSV 파일을 입력해 실제 데이터를 분석합니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("내 데이터 입력하러 가기", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()


def render_summary_cards(info, result):
    dq = data_quality_summary(result["df"])
    issues = core_issues(result)
    issue_text = ", ".join(issues[:2]) if issues else "큰 이상 패턴 없음"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wattda 점수", f"{result['score']}/100")
    c2.metric("예상 월 절감액", f"{krw(result['total_saving_low'])} ~ {krw(result['total_saving_high'])}")
    c3.metric("핵심 문제", issue_text)
    c4.metric("데이터 품질", f"{dq['score']}/100")


def render_professional_kpi_cards(info, result):
    kpis = professional_kpis(info, result)
    st.markdown("### 전문 진단 지표")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("전력 EUI", f"{kpis['electric_eui']:.1f} kWh/㎡·년")
    k2.metric("부하율", pct(kpis["load_factor"]))
    k3.metric("기저부하 비중", pct(kpis["baseload_ratio"]))
    k4.metric("계약전력 사용률", pct(kpis["contract_utilization"]))

    with st.expander("전문 지표 해석 보기"):
        st.write(f"**부하율:** {kpis['load_factor_comment']}")
        st.write(f"**기저부하:** {kpis['baseload_comment']}")
        st.write(f"**계약전력:** {kpis['contract_comment']}")
        st.caption("전문 지표는 예비 진단용입니다. 실제 절감 성과는 개선 전후 데이터를 비교해 검증해야 합니다.")


def render_result_graphs(result):
    df = result["df"]

    st.markdown("### 전력 사용 패턴")
    today_df, display_date, used_fallback = get_today_df_for_display(df)
    if used_fallback:
        st.caption(f"오늘 데이터가 없어 데이터에 포함된 가장 최근 날짜({display_date})를 표시합니다.")

    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"#### 하루 전력 사용량 | {display_date}")
        st.line_chart(today_df.set_index("시각")[[COL_KWH]], height=260)

    with g2:
        monthly = df.copy()
        monthly["월"] = monthly[COL_DT].dt.to_period("M").astype(str)
        monthly_summary = monthly.groupby("월", as_index=False)[COL_KWH].sum()
        st.markdown("#### 월별 전력 사용량")
        st.bar_chart(monthly_summary.set_index("월")[[COL_KWH]], height=260)

    if COL_IN in today_df.columns or COL_OUT in today_df.columns:
        st.markdown("#### 실내외 온도 추이")
        temp_cols = []
        if COL_IN in today_df.columns:
            temp_cols.append(COL_IN)
        if COL_OUT in today_df.columns:
            temp_cols.append(COL_OUT)
        st.line_chart(today_df.set_index("시각")[temp_cols], height=260)


def render_detail_diagnosis(info, result):
    st.markdown("### 상세 진단")
    st.caption("각 항목은 문제, 원인 추정, 조치, 검증 방법 중심으로 정리됩니다.")

    for i, block in enumerate(diagnosis_blocks(info, result), start=1):
        with st.expander(f"{i}. {block['제목']}", expanded=(i <= 2)):
            st.markdown(f"**문제**  \n{block['문제']}")
            st.markdown(f"**원인 추정**  \n{block['원인']}")
            st.markdown(f"**비용 영향**  \n{block['비용']}")
            st.markdown(f"**바로 할 조치**  \n{block['조치']}")
            st.markdown(f"**다음 달 확인 방법**  \n{block['확인']}")


def render_recommendation_section(info, result):
    st.markdown("### 우선 개선 조치")
    rec_df = recommendation_rows_professional(info, result)
    st.dataframe(rec_df, width="stretch", hide_index=True)


def render_report_downloads(info, result):
    st.markdown("### 리포트 다운로드")
    st.caption("진단 결과를 Markdown, HTML, PDF 형식으로 저장할 수 있습니다.")

    md = markdown_report(info, result)
    html_doc = html_report(info, result)
    pdf_doc = pdf_bytes(info, result)

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            "Markdown 다운로드",
            data=md.encode("utf-8-sig"),
            file_name="wattda_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "HTML 다운로드",
            data=html_doc.encode("utf-8-sig"),
            file_name="wattda_report.html",
            mime="text/html",
            use_container_width=True,
        )
    with d3:
        if pdf_doc:
            st.download_button(
                "PDF 다운로드",
                data=pdf_doc,
                file_name="wattda_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.warning("PDF 기능을 사용하려면 reportlab이 필요합니다.")


def save_building_info_from_form(info):
    st.markdown("### 건물 정보")
    st.caption("건물의 기본 정보, 위치, 운영시간, 요금 정보를 입력하세요. 주소를 입력하면 해당 좌표를 기반으로 실시간 기상정보가 연결됩니다.")

    with st.container():
        st.markdown(
            """
            <div class="w-form-section">
                <div class="w-form-section-title">기본 정보</div>
                <div class="w-form-section-desc">업종별 전력 사용 특성을 구분하기 위한 기본 정보입니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        b1, b2 = st.columns(2)
        with b1:
            건물명 = st.text_input("건물명", info["건물명"])
        with b2:
            building_options = [
                "카페",
                "음식점/식당",
                "베이커리",
                "편의점/소매점",
                "학원/교육시설",
                "스터디카페/독서실",
                "피트니스센터",
                "병원/의원",
                "사무실",
                "숙박시설",
                "상가/복합매장",
                "기타",
            ]
            current_type = info.get("건물용도", "카페")
            old_type_map = {
                "학원": "학원/교육시설",
                "중소형 오피스": "사무실",
                "상가": "상가/복합매장",
            }
            current_type = old_type_map.get(current_type, current_type)
            if current_type not in building_options:
                current_type = "카페"
            건물용도 = st.selectbox("건물 용도", building_options, index=building_options.index(current_type))

        st.caption(
            "주요 대상은 카페, 음식점, 소매점, 학원, 스터디카페, 병원, 사무실처럼 전력 사용 패턴이 비교적 뚜렷한 중소형 상업시설입니다."
        )

    with st.container():
        st.markdown(
            """
            <div class="w-form-section">
                <div class="w-form-section-title">위치 정보</div>
                <div class="w-form-section-desc">건물 주소를 입력하거나 지도에서 위치를 클릭하세요. 선택 위치는 실시간 외기 조건 조회에 사용됩니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        건물주소, 지도기준도시, 위도, 경도 = render_address_location_picker(info)
        지역 = 건물주소

    with st.container():
        st.markdown(
            """
            <div class="w-form-section">
                <div class="w-form-section-title">규모 및 요금 정보</div>
                <div class="w-form-section-desc">전력 EUI, 평균 단가, 계약전력 사용률 계산에 사용됩니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        s1, s2, s3 = st.columns(3)
        with s1:
            연면적 = st.number_input("연면적 ㎡", min_value=10, value=int(info["연면적"]), step=10)
            월전기요금 = st.number_input("월 전기요금 원", min_value=0, value=int(info["월전기요금"]), step=10000)
        with s2:
            층수 = st.number_input("층수", min_value=1, value=int(info["층수"]), step=1)
            월전력사용량 = st.number_input("월 전력사용량 kWh", min_value=1, value=int(info["월전력사용량"]), step=100)
        with s3:
            계약전력 = st.number_input("계약전력 kW", min_value=1, value=int(info["계약전력"]), step=1)
            요금종별 = st.selectbox("요금 종별", ["일반용 전력 갑", "일반용 전력 을", "교육용", "산업용", "기타"], index=0)

        냉방방식 = st.selectbox("냉방 방식", ["시스템에어컨", "개별 에어컨", "중앙 냉방", "냉방 없음", "기타"], index=0)

    with st.container():
        st.markdown(
            """
            <div class="w-form-section">
                <div class="w-form-section-title">요일별 운영시간</div>
                <div class="w-form-section-desc">운영 체크 후 시작과 종료 시간을 선택하세요. 각 요일을 한 줄로 정리했습니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        default_schedule = info.get("운영스케줄", {})
        schedule_inputs = {}

        for day in ["월", "화", "수", "목", "금", "토", "일"]:
            base_day = {
                "운영": day in info.get("운영요일", []),
                "시작": info.get("운영시작", time(9, 0)),
                "종료": info.get("운영종료", time(18, 0)),
            }
            base_day.update(default_schedule.get(day, {}))

            r1, r2, r3 = st.columns([0.25, 0.375, 0.375])
            with r1:
                운영 = st.checkbox(day, value=bool(base_day.get("운영", False)), key=f"op_{day}_v05")
            with r2:
                시작 = st.time_input(
                    "시작",
                    value=base_day.get("시작", time(9, 0)),
                    key=f"start_{day}_v05",
                    disabled=not 운영,
                    label_visibility="collapsed",
                )
            with r3:
                종료 = st.time_input(
                    "종료",
                    value=base_day.get("종료", time(18, 0)),
                    key=f"end_{day}_v05",
                    disabled=not 운영,
                    label_visibility="collapsed",
                )

            schedule_inputs[day] = {"운영": 운영, "시작": 시작, "종료": 종료}

        운영요일 = [day for day, setting in schedule_inputs.items() if setting["운영"]]
        운영시작 = schedule_inputs[운영요일[0]]["시작"] if 운영요일 else time(9, 0)
        운영종료 = schedule_inputs[운영요일[0]]["종료"] if 운영요일 else time(18, 0)

    if st.button("건물 정보 저장하고 다음 단계로", type="primary", use_container_width=True):
        st.session_state.info = {
            "건물명": 건물명,
            "건물용도": 건물용도,
            "지역": 지역,
            "건물주소": 건물주소,
            "지도기준도시": 지도기준도시,
            "위도": 위도,
            "경도": 경도,
            "연면적": 연면적,
            "층수": 층수,
            "운영요일": 운영요일,
            "운영시작": 운영시작,
            "운영종료": 운영종료,
            "운영스케줄": schedule_inputs,
            "월전기요금": 월전기요금,
            "월전력사용량": 월전력사용량,
            "계약전력": 계약전력,
            "요금종별": 요금종별,
            "냉방방식": 냉방방식,
        }
        refresh_analysis()
        st.session_state.current_step = 2
        st.success("건물 정보가 저장되었습니다.")
        st.rerun()


def render_data_input_page():
    st.markdown("### 데이터 입력")
    st.caption("처음에는 샘플 데이터로 체험하고, 이후 실제 CSV 데이터를 업로드하는 흐름을 추천합니다.")

    mode = st.radio("입력 방식", ["샘플 데이터 사용", "CSV 업로드"], horizontal=True)

    if mode == "샘플 데이터 사용":
        st.markdown(
            """
            <div class="w-summary-box">
            샘플 데이터에는 1년치 시간별 전력사용량과 실외온도, 실내온도, 상대습도, 점유인원 컬럼이 포함되어 있습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("샘플 데이터 적용하고 진단 결과 보기", type="primary", use_container_width=True):
            st.session_state.data = make_sample_data()
            refresh_analysis()
            st.session_state.current_step = 3
            st.rerun()

    else:
        st.markdown("#### CSV 업로드")
        st.write(f"필수 컬럼: `{COL_DT}`, `{COL_KWH}`")
        st.write(f"권장 컬럼: `{COL_OUT}`, `{COL_IN}`, `{COL_RH}`, `{COL_OCC}`")

        uploaded = st.file_uploader("CSV 파일 업로드", type=["csv"])
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
                required = {COL_DT, COL_KWH}
                if not required.issubset(df.columns):
                    st.error(f"CSV에는 {COL_DT}와 {COL_KWH} 컬럼이 반드시 필요합니다.")
                else:
                    df[COL_DT] = pd.to_datetime(df[COL_DT], errors="coerce")
                    df[COL_KWH] = pd.to_numeric(df[COL_KWH], errors="coerce")

                    for col in [COL_OUT, COL_IN, COL_RH, COL_OCC]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")

                    df = df.dropna(subset=[COL_DT, COL_KWH])
                    if df.empty:
                        st.error("유효한 일시와 전력사용량 데이터가 없습니다. CSV 날짜 형식과 숫자 형식을 확인해 주세요.")
                    else:
                        st.session_state.data = prepare_data(df)
                        refresh_analysis()
                        st.success("CSV 업로드가 완료되었고 진단 결과가 갱신되었습니다.")
                        if st.button("진단 결과 보기", type="primary", use_container_width=True):
                            st.session_state.current_step = 3
                            st.rerun()
            except Exception as e:
                st.error(f"CSV 처리 중 오류가 발생했습니다: {e}")

    with st.expander("CSV 컬럼 가이드 보기"):
        guide_df = pd.DataFrame(
            [
                [COL_DT, "필수", "2026-08-01 13:00", "시간 기준 분석"],
                [COL_KWH, "필수", "41.8", "전력 사용량 분석"],
                [COL_OUT, "권장", "31.2", "실외온도와 냉방 민감도"],
                [COL_IN, "권장", "25.6", "실내온도와 쾌적성"],
                [COL_RH, "권장", "58.0", "실내 습도 상태"],
                [COL_OCC, "권장", "72", "점유 대비 전력 사용"],
            ],
            columns=["컬럼명", "구분", "예시", "분석 활용"],
        )
        st.dataframe(guide_df, width="stretch", hide_index=True)

    st.markdown("#### 현재 데이터 미리보기")
    st.dataframe(st.session_state.data.head(40), width="stretch")
    preview_result = analyze(st.session_state.data, st.session_state.info)
    render_data_quality_box(preview_result)


def render_results_page():
    info = st.session_state.info
    result = st.session_state.result

    render_current_weather_box(info)

    st.markdown("### 핵심 요약")
    render_summary_cards(info, result)

    issues = core_issues(result)
    st.markdown("#### 핵심 문제")
    for issue in issues:
        st.markdown(f'<span class="w-pill">{issue}</span>', unsafe_allow_html=True)

    render_professional_kpi_cards(info, result)

    with st.expander("데이터 품질 자세히 보기", expanded=False):
        render_data_quality_box(result)

    render_result_graphs(result)
    render_detail_diagnosis(info, result)
    render_recommendation_section(info, result)
    render_report_downloads(info, result)



# ============================================================
# Layout
# ============================================================

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

st.sidebar.title("⚡ Wattda")
st.sidebar.caption("건물 전기요금 전문 진단")
st.sidebar.divider()
st.sidebar.markdown("### 진행 단계")

side_steps = {
    "진단 시작": 0,
    "건물 정보": 1,
    "데이터 입력": 2,
    "진단 결과": 3,
}

step_labels = list(side_steps.keys())
current_step = st.session_state.get("current_step", 0)
if current_step not in list(side_steps.values()):
    current_step = 0

current_index = list(side_steps.values()).index(current_step)

selected_label = st.sidebar.radio(
    "진행 단계 선택",
    step_labels,
    index=current_index,
    label_visibility="collapsed",
)

selected_step = side_steps[selected_label]
if selected_step != st.session_state.current_step:
    st.session_state.current_step = selected_step
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("제작자: 소정호")
st.sidebar.caption("Netlify 랜딩페이지에서 연결되는 진단 도구입니다.")

render_top_header()

if st.session_state.current_step == 0:
    render_step_bar(1)
    st.markdown("## 진단을 시작하세요")
    st.write(
        """
        이미 서비스 소개는 랜딩페이지에서 확인했으므로, 이 화면에서는 바로 진단을 시작할 수 있도록 구성했습니다.
        샘플 데이터로 빠르게 체험하거나, 실제 건물 정보를 입력해 진단을 진행하세요.
        """
    )
    render_quick_start_cards()

    st.markdown("### 진단 흐름")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(
            """
            <div class="w-card">
                <h3>1. 건물 정보</h3>
                <p class="w-muted">건물 용도, 주소, 면적, 운영시간, 요금정보를 입력합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f2:
        st.markdown(
            """
            <div class="w-card">
                <h3>2. 전력 데이터</h3>
                <p class="w-muted">샘플 데이터 또는 CSV 파일을 사용해 시간별 전력 패턴을 분석합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with f3:
        st.markdown(
            """
            <div class="w-card">
                <h3>3. 진단 결과</h3>
                <p class="w-muted">절감 가능액, 전문 지표, 상세 진단, 리포트를 확인합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif st.session_state.current_step == 1:
    render_step_bar(1)
    save_building_info_from_form(st.session_state.info)

elif st.session_state.current_step == 2:
    render_step_bar(2)
    render_data_input_page()

elif st.session_state.current_step == 3:
    render_step_bar(3)
    render_results_page()

import streamlit as st
import pandas as pd
import numpy as np
from datetime import time
import io
import os
import html
import base64
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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

## 3. 상세 진단 요약
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
    text += "\n## 4. 우선 개선 조치\n"
    for _, row in rec_df.iterrows():
        text += f"{row['우선순위']}. {row['개선 조치']} | 예상 효과: {row['예상 효과']} | 난이도: {row['난이도']}\n"

    text += """

## 5. 간략 그래프 요약
아래 그래프는 오늘 하루 전력 사용량과 월별 전력 사용량을 보여줍니다. 하루 중 사용 패턴과 연간 월별 사용 흐름을 함께 확인하기 위한 요약 그래프입니다.
"""
    return text


def report_reference_text():
    return """
## 6. 참고
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
# Layout
# ============================================================

st.sidebar.title("⚡ Wattda")
st.sidebar.caption("무료 건물 전기요금 진단 MVP")
page = st.sidebar.radio(
    "메뉴",
    [
        "서비스 소개",
        "건물 정보 입력",
        "데이터 입력",
        "진단 대시보드",
        "상세 진단",
        "리포트 다운로드",
    ],
)
st.sidebar.divider()
st.sidebar.caption("Wattda v0.1 Free MVP")

st.markdown(
    """
    <div class="w-hero">
        <div class="w-badge">무료 MVP | 건물 전기요금 진단 서비스</div>
        <div class="w-title-row">
            <h1>Wattda</h1>
            <div class="w-author">제작자: 소정호</div>
        </div>
        <p>시간별 전력 데이터를 바탕으로 건물의 전기요금 낭비 요인, 피크 시간대, 예상 절감액, 개선 조치를 자동으로 분석하는 무료 MVP 서비스입니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Pages
# ============================================================

if page == "서비스 소개":
    info = st.session_state.info
    result = st.session_state.result

    st.markdown("## 전기요금이 왜 많이 나왔는지 자동으로 진단합니다")
    st.write(
        """
        Wattda는 건물의 시간별 전력 사용 데이터를 바탕으로
        야간 기저부하, 휴무일 전력 낭비, 냉방 민감도, 피크 시간대를 분석하고
        예상 절감액과 개선 조치를 자동으로 제안하는 무료 MVP 서비스입니다.
        """
    )

    st.info("현재 버전은 무료 MVP입니다. 분석 결과는 예비 진단 및 테스트 목적으로 활용해 주세요.")
    st.caption("현재 표시되는 결과는 기본 샘플 데이터를 기준으로 계산된 예시 결과입니다.")

    st.markdown("### 무엇을 분석하나요?")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="w-card">
                <h3>전력 낭비 탐지</h3>
                <p class="w-muted">야간, 휴무일, 저점유 시간대의 불필요한 전력 사용을 찾습니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="w-card">
                <h3>피크 시간 분석</h3>
                <p class="w-muted">전력 사용량이 가장 높은 시간대를 찾아 운영 원인을 추정합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="w-card">
                <h3>절감액 추정</h3>
                <p class="w-muted">야간 부하, 휴무일 부하, 냉방 최적화를 기준으로 절감 가능액을 계산합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 현재 샘플 진단 결과")

    m1, m2, m3 = st.columns(3)
    m1.metric("Wattda 점수", f"{result['score']}/100")
    m2.metric("진단 등급", f"{result['grade']} | {result['risk']}")
    m3.metric("예상 월 절감액", f"{krw(result['total_saving_low'])} ~ {krw(result['total_saving_high'])}")

    st.markdown("### 사용 순서")
    st.markdown(
        """
        1. **건물 정보 입력**에서 건물 용도, 면적, 운영시간, 전기요금을 입력합니다.  
        2. **데이터 입력**에서 샘플 데이터를 사용하거나 CSV를 업로드합니다.  
        3. **진단 대시보드**에서 전력 사용 패턴을 확인합니다.  
        4. **상세 진단**에서 문제 원인과 개선 조치를 확인합니다.  
        5. **리포트 다운로드**에서 Markdown, HTML, PDF 리포트를 저장합니다.
        """
    )

    st.markdown("### 분석에 사용하는 데이터")
    st.write(
        "기본 분석에는 일시와 전력사용량이 필요합니다. 실외온도, 실내온도, 상대습도, 점유인원을 함께 입력하면 진단 품질이 높아집니다."
    )

    st.dataframe(
        pd.DataFrame(
            [
                [COL_DT, "필수", "시간 기준 분석, 피크, 야간, 주말 판별"],
                [COL_KWH, "필수", "전력 사용량 분석"],
                [COL_OUT, "권장", "냉방 민감도 분석"],
                [COL_IN, "권장", "실내온도와 쾌적성 진단"],
                [COL_RH, "권장", "실내 습도 관리 진단"],
                [COL_OCC, "권장", "점유 대비 전력 사용 진단"],
            ],
            columns=["컬럼명", "중요도", "용도"],
        ),
        width="stretch",
        hide_index=True,
    )

elif page == "건물 정보 입력":
    st.subheader("건물 정보 입력")
    info = st.session_state.info

    col1, col2 = st.columns([1.05, 0.95])

    with col1:
        건물명 = st.text_input("건물명", info["건물명"])
        건물용도 = st.selectbox(
            "건물 용도",
            ["학원", "스터디카페", "피트니스센터", "병원/의원", "중소형 오피스", "상가", "기타"],
            index=["학원", "스터디카페", "피트니스센터", "병원/의원", "중소형 오피스", "상가", "기타"].index(info["건물용도"]) if info["건물용도"] in ["학원", "스터디카페", "피트니스센터", "병원/의원", "중소형 오피스", "상가", "기타"] else 0,
        )
        지역 = st.text_input("지역", info["지역"])
        연면적 = st.number_input("연면적 ㎡", min_value=10, value=int(info["연면적"]), step=10)
        층수 = st.number_input("층수", min_value=1, value=int(info["층수"]), step=1)
        st.markdown("#### 요일별 운영시간")
        st.caption("요일마다 운영시간이 다를 수 있으므로 각 요일별로 따로 설정할 수 있습니다.")

        default_schedule = info.get("운영스케줄", {})
        schedule_inputs = {}
        day_cols = st.columns(2)
        for idx, day in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
            base = default_schedule.get(day, {"운영": day in info.get("운영요일", []), "시작": info.get("운영시작", time(9, 0)), "종료": info.get("운영종료", time(18, 0))})
            with day_cols[idx % 2]:
                운영 = st.checkbox(f"{day}요일 운영", value=bool(base.get("운영", False)), key=f"op_{day}")
                시작 = st.time_input(f"{day} 시작", value=base.get("시작", time(9, 0)), key=f"start_{day}", disabled=not 운영)
                종료 = st.time_input(f"{day} 종료", value=base.get("종료", time(18, 0)), key=f"end_{day}", disabled=not 운영)
            schedule_inputs[day] = {"운영": 운영, "시작": 시작, "종료": 종료}

        운영요일 = [day for day, setting in schedule_inputs.items() if setting["운영"]]
        운영시작 = schedule_inputs[운영요일[0]]["시작"] if 운영요일 else time(9, 0)
        운영종료 = schedule_inputs[운영요일[0]]["종료"] if 운영요일 else time(18, 0)

        월전기요금 = st.number_input("월 전기요금 원", min_value=0, value=int(info["월전기요금"]), step=10000)
        월전력사용량 = st.number_input("월 전력사용량 kWh", min_value=1, value=int(info["월전력사용량"]), step=100)
        계약전력 = st.number_input("계약전력 kW", min_value=1, value=int(info["계약전력"]), step=1)
        요금종별 = st.selectbox("요금 종별", ["일반용 전력 갑", "일반용 전력 을", "교육용", "산업용", "기타"], index=0)
        냉방방식 = st.selectbox("냉방 방식", ["시스템에어컨", "개별 에어컨", "중앙 냉방", "냉방 없음", "기타"], index=0)

        if st.button("저장하고 다시 분석", type="primary"):
            st.session_state.info = {
                "건물명": 건물명,
                "건물용도": 건물용도,
                "지역": 지역,
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
            st.success("건물 정보가 저장되었고 진단 결과가 갱신되었습니다.")

    with col2:
        st.markdown("### 3D 건물 미리보기")
        preview_info = {
            "건물명": 건물명,
            "건물용도": 건물용도,
            "지역": 지역,
            "연면적": 연면적,
            "층수": 층수,
        }
        fig = draw_building_preview_3d(preview_info)
        st.pyplot(fig, clear_figure=True)
        st.caption("입력한 규모를 바탕으로 생성한 단순 3D 건물 미리보기입니다. 고객 설명용 개념 화면으로 활용할 수 있습니다.")

elif page == "데이터 입력":
    st.subheader("전력 데이터 입력")

    st.info(
        """
        처음 사용하는 경우에는 먼저 '샘플 데이터 사용'을 선택해 전체 진단 흐름을 확인하세요.
        실제 건물 데이터를 분석하려면 CSV 업로드를 선택하고 필수 컬럼인 일시와 전력사용량(kWh)을 포함해 주세요.
        """
    )
    st.warning("현재 기본값은 샘플 데이터입니다. 실제 진단을 원하면 CSV 업로드를 사용해 주세요.")

    mode = st.radio("입력 방식", ["샘플 데이터 사용", "CSV 업로드"], horizontal=True)

    if mode == "샘플 데이터 사용":
        st.write("샘플 데이터에는 1년치 시간별 데이터가 들어 있으며, 전력 데이터 외에 실외온도, 실내온도, 상대습도, 점유인원 컬럼이 포함되어 있습니다. 1년치 시간별 데이터는 약 8,760행이라 앱에서 충분히 다룰 수 있습니다.")
        if st.button("샘플 데이터 다시 불러오기", type="primary"):
            st.session_state.data = make_sample_data()
            refresh_analysis()
            st.success("샘플 데이터가 적용되었습니다.")
    else:
        st.write(f"필수 컬럼: {COL_DT}, {COL_KWH}")
        st.write(f"권장 컬럼: {COL_OUT}, {COL_IN}, {COL_RH}, {COL_OCC}")
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

                    optional_numeric_cols = [COL_OUT, COL_IN, COL_RH, COL_OCC]
                    for col in optional_numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce")

                    df = df.dropna(subset=[COL_DT, COL_KWH])

                    if df.empty:
                        st.error("유효한 일시와 전력사용량 데이터가 없습니다. CSV 날짜 형식과 숫자 형식을 확인해 주세요.")
                        st.stop()

                    st.session_state.data = prepare_data(df)
                    refresh_analysis()
                    st.success("CSV 업로드가 완료되었고 진단 결과가 갱신되었습니다.")
            except Exception as e:
                st.error(f"CSV 처리 중 오류가 발생했습니다: {e}")

    st.markdown("### 컬럼 가이드")
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

    st.markdown("### 현재 데이터 미리보기")
    st.dataframe(st.session_state.data.head(80), width="stretch")

    st.download_button(
        "현재 데이터 CSV 다운로드",
        data=st.session_state.data.to_csv(index=False).encode("utf-8-sig"),
        file_name="wattda_sample_data_v01.csv",
        mime="text/csv",
    )

elif page == "진단 대시보드":
    st.subheader("진단 대시보드")
    info = st.session_state.info
    result = st.session_state.result
    df = result["df"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Wattda 점수", f"{result['score']}/100")
    col2.metric("진단 등급", f"{result['grade']} | {result['risk']}")
    col3.metric("월 전기요금", krw(info["월전기요금"]))
    col4.metric("평균 단가", f"{result['unit_price']:.1f}원/kWh")

    st.markdown("### 핵심 문제")
    for issue in core_issues(result):
        st.markdown(f'<span class="w-pill">{issue}</span>', unsafe_allow_html=True)

    # 한국 기준 오늘 날짜의 0시부터 24시까지 표시
    today_kst = pd.Timestamp.now(tz="Asia/Seoul").date()
    today_df = df[df[COL_DT].dt.date == today_kst].copy()
    display_date = today_kst

    if today_df.empty:
        display_date = df[COL_DT].dt.date.max()
        today_df = df[df[COL_DT].dt.date == display_date].copy()
        st.warning(f"오늘 날짜({today_kst}) 데이터가 없어, 데이터에 포함된 가장 최근 날짜({display_date})를 표시합니다.")

    today_df = today_df.sort_values(COL_DT)
    today_df["시각"] = today_df[COL_DT].dt.hour

    st.markdown(f"### 오늘 하루 전력 사용량 | {display_date}")
    st.caption("한국 시간 기준 0시부터 24시까지의 하루 전력 사용량입니다.")
    st.line_chart(today_df.set_index("시각")[[COL_KWH]], height=300)

    metric_cols = st.columns(4)
    metric_cols[0].metric("오늘 총 전력사용량", kwh(today_df[COL_KWH].sum()))
    metric_cols[1].metric("오늘 최대 시간 사용량", kwh(today_df[COL_KWH].max()))
    metric_cols[2].metric("야간 사용 비율", pct(result["night_ratio"]))
    metric_cols[3].metric("주말 사용 비율", pct(result["weekend_ratio"]))

    if COL_IN in today_df.columns or COL_OUT in today_df.columns:
        st.markdown(f"### 오늘 하루 실내외 온도 추이 | {display_date}")
        st.caption("한국 시간 기준 0시부터 24시까지의 실내온도와 실외온도 변화입니다. 빨간색 선은 실외온도입니다.")
        temp_cols = []
        if COL_IN in today_df.columns:
            temp_cols.append(COL_IN)
        if COL_OUT in today_df.columns:
            temp_cols.append(COL_OUT)
        st.line_chart(
            today_df.set_index("시각")[temp_cols],
            height=300,
            color=["#2563EB", "#EF4444"][:len(temp_cols)],
        )

    st.markdown("### 월별 전력 사용량")
    monthly = df.copy()
    monthly["월"] = monthly[COL_DT].dt.to_period("M").astype(str)
    monthly_summary = monthly.groupby("월", as_index=False)[COL_KWH].sum()
    monthly_summary["예상전기요금(원)"] = monthly_summary[COL_KWH] * result["unit_price"]

    year_cols = st.columns(3)
    year_cols[0].metric("분석 기간 총 전력사용량", kwh(monthly_summary[COL_KWH].sum()))
    year_cols[1].metric("분석 기간 예상 전기요금", krw(monthly_summary["예상전기요금(원)"].sum()))
    year_cols[2].metric("월평균 전력사용량", kwh(monthly_summary[COL_KWH].mean()))

    st.bar_chart(monthly_summary.set_index("월")[[COL_KWH]], height=260, color="#2563EB")

    if COL_IN in df.columns or COL_OUT in df.columns:
        st.markdown("### 월별 평균 실내외 온도")
        monthly_temp = df.copy()
        monthly_temp["월"] = monthly_temp[COL_DT].dt.month
        monthly_temp_summary = monthly_temp.groupby("월", as_index=False).agg({
            COL_IN: "mean" if COL_IN in monthly_temp.columns else "size",
            COL_OUT: "mean" if COL_OUT in monthly_temp.columns else "size",
        })

        temp_col1, temp_col2 = st.columns(2)
        if COL_IN in monthly_temp_summary.columns:
            with temp_col1:
                st.caption("월별 평균 실내온도")
                st.bar_chart(monthly_temp_summary.set_index("월")[[COL_IN]], height=260, color="#2563EB")
        if COL_OUT in monthly_temp_summary.columns:
            with temp_col2:
                st.caption("월별 평균 실외온도")
                st.bar_chart(monthly_temp_summary.set_index("월")[[COL_OUT]], height=260, color="#EF4444")

    st.markdown("### 절감액 추정")
    s1, s2, s3 = st.columns(3)
    s1.metric("야간 절감 가능액", krw(result["night_saving"]))
    s2.metric("주말 절감 가능액", krw(result["weekend_saving"]))
    s3.metric("냉방 최적화", f"{krw(result['cooling_saving_low'])} ~ {krw(result['cooling_saving_high'])}")

    money_card("총 월 절감 가능액", f"{krw(result['total_saving_low'])} ~ {krw(result['total_saving_high'])}")

elif page == "상세 진단":
    st.subheader("상세 진단")
    info = st.session_state.info
    result = st.session_state.result
    blocks = diagnosis_blocks(info, result)

    st.markdown(
        """
        <div class="w-summary-box">
        상세 진단은 문제, 원인 추정, 비용 영향, 바로 할 조치, 다음 달 확인 방법 순서로 정리합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for block in blocks:
        st.markdown(f"### {block['제목']}")
        st.markdown(f"**문제**  \n{block['문제']}")
        st.markdown(f"**원인 추정**  \n{block['원인']}")
        st.markdown(f"**비용 영향**  \n{block['비용']}")
        st.markdown(f"**바로 할 조치**  \n{block['조치']}")
        st.markdown(f"**다음 달 확인 방법**  \n{block['확인']}")
        st.divider()

    st.markdown("### 우선 개선 조치")
    st.dataframe(recommendations(result), width="stretch", hide_index=True)

elif page == "리포트 다운로드":
    st.subheader("리포트 다운로드")

    st.info(
        """
        진단 결과를 Markdown, HTML, PDF 형식으로 저장할 수 있습니다.
        무료 MVP 버전에서는 기본 샘플 데이터 또는 업로드한 CSV 데이터를 기준으로 리포트가 생성됩니다.
        """
    )
    info = st.session_state.info
    result = st.session_state.result
    md = markdown_report(info, result)

    top_metrics = st.columns(3)
    top_metrics[0].metric("진단 점수", f"{result['score']}/100")
    top_metrics[1].metric("진단 등급", f"{result['grade']} | {result['risk']}")
    top_metrics[2].metric("핵심 문제 수", f"{len(core_issues(result))}개")
    money_card("월 절감 가능액", f"{krw(result['total_saving_low'])} ~ {krw(result['total_saving_high'])}")

    st.markdown("### 리포트 미리보기")
    st.markdown(build_report_body(info, result))

    st.caption("오늘 하루 전력 사용량")
    today_df, display_date, _ = get_today_df_for_display(result["df"])
    st.line_chart(today_df.set_index("시각")[[COL_KWH]], height=260)

    st.caption("월별 전력 사용량")
    report_monthly = result["df"].copy()
    report_monthly["월"] = report_monthly[COL_DT].dt.to_period("M").astype(str)
    report_monthly_summary = report_monthly.groupby("월", as_index=False)[COL_KWH].sum()
    st.bar_chart(report_monthly_summary.set_index("월")[[COL_KWH]], height=260, color="#2563EB")

    st.markdown("### 6. 참고")
    st.write("이 리포트는 시간별 전력 데이터와 건물 기본정보를 바탕으로 생성된 운영 진단 결과입니다. 실제 절감액은 운영 방식, 요금제, 계절 조건에 따라 달라질 수 있습니다.")

    st.divider()
    st.download_button(
        "Markdown 리포트 다운로드",
        data=md.encode("utf-8-sig"),
        file_name="wattda_report_v01.md",
        mime="text/markdown",
    )

    html_text = html_report(info, result)
    st.download_button(
        "HTML 리포트 다운로드",
        data=html_text.encode("utf-8-sig"),
        file_name="wattda_report_v01.html",
        mime="text/html",
    )

    pdf = pdf_bytes(info, result)
    if pdf:
        st.download_button(
            "PDF 리포트 다운로드",
            data=pdf,
            file_name="wattda_report_v01.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("PDF 생성을 위해 reportlab 설치가 필요합니다. 설치 명령어: py -m pip install reportlab")

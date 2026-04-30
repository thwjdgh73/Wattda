import streamlit as st
import pandas as pd
import numpy as np
from datetime import time
import io, os, html

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="Wattda | 전기요금 진단 AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{padding-top:1.2rem;max-width:1180px}.hero{padding:24px 26px;border-radius:22px;background:linear-gradient(135deg,#111827,#374151);color:white;margin-bottom:18px}.hero h1{font-size:42px;margin:0 0 6px}.hero p{font-size:17px;line-height:1.6;margin:0}.muted{color:#6b7280}.card{padding:16px;border:1px solid #e5e7eb;border-radius:16px;background:white;margin-bottom:12px}
</style>
""", unsafe_allow_html=True)

# ---------------- helpers ----------------
def krw(v):
    try: return f"{int(round(float(v))):,}원"
    except Exception: return "0원"
def man(v):
    try: return f"{float(v)/10000:,.1f}만 원"
    except Exception: return "0만 원"
def kwh(v):
    try: return f"{float(v):,.1f} kWh"
    except Exception: return "0.0 kWh"
def pct(v):
    try: return f"{float(v):.1f}%"
    except Exception: return "0.0%"
def div(a,b,d=0):
    try:
        return d if b==0 or pd.isna(b) else a/b
    except Exception:
        return d

# ---------------- sample data ----------------
def sample_data(year=2026, month=8):
    start=pd.Timestamp(year=year,month=month,day=1,hour=0)
    end=start+pd.offsets.MonthEnd(1)+pd.Timedelta(hours=23)
    idx=pd.date_range(start,end,freq="h")
    rng=np.random.default_rng(7)
    rows=[]
    for dt in idx:
        hour=dt.hour; wd=dt.weekday()
        temp=27.5+4.2*np.sin((hour-8)/24*2*np.pi)+(2.2 if dt.day in [5,6,7,8,18,19,20,21] else 0)+rng.normal(0,.65)
        operating=wd in [0,1,2,3,4,5] and 13<=hour<22
        load=15.5
        if operating:
            load+=31
            if 15<=hour<=21: load+=9
        if temp>26:
            cool=(temp-26)*5.0
            load += cool if operating else cool*.33
        if operating and 14<=hour<=17: load+=7
        if wd==6:
            load+=9
            if 12<=hour<=20: load+=7
        if hour>=22 or hour<6: load+=5.5
        load=max(load+rng.normal(0,2.0),7)
        rows.append({"DateTime":dt,"Electricity_kWh":round(load,2),"Outdoor_Temperature":round(temp,1)})
    return pd.DataFrame(rows)

def prep(df):
    df=df.copy(); df["DateTime"]=pd.to_datetime(df["DateTime"]); df=df.sort_values("DateTime")
    df["Hour"]=df["DateTime"].dt.hour; df["Date"]=df["DateTime"].dt.date; df["Weekday"]=df["DateTime"].dt.weekday
    df["IsWeekend"]=df["Weekday"].isin([5,6]); df["IsSunday"]=df["Weekday"].eq(6)
    return df

# ---------------- analysis ----------------
def analyze(df, info):
    df=prep(df)
    day_map={"월":0,"화":1,"수":2,"목":3,"금":4,"토":5,"일":6}
    op_days=[day_map[d] for d in info["operating_days"] if d in day_map]
    s=info["operating_start"].hour; e=info["operating_end"].hour
    if s<e: df["IsOperatingHour"]=df["Weekday"].isin(op_days)&(df["Hour"]>=s)&(df["Hour"]<e)
    else: df["IsOperatingHour"]=df["Weekday"].isin(op_days)&((df["Hour"]>=s)|(df["Hour"]<e))
    df["IsNight"]=(df["Hour"]>=22)|(df["Hour"]<6)
    bill=float(info["monthly_bill"]); mkwh=float(info["monthly_kwh"]); unit=div(bill,mkwh,div(bill,df["Electricity_kWh"].sum(),0))
    op_avg=df.loc[df["IsOperatingHour"],"Electricity_kWh"].mean(); night_avg=df.loc[df["IsNight"],"Electricity_kWh"].mean()
    night_ratio=div(night_avg,op_avg)*100
    weekday_daily=df.loc[~df["IsWeekend"]].groupby("Date")["Electricity_kWh"].sum().mean()
    weekend_daily=df.loc[df["IsWeekend"]].groupby("Date")["Electricity_kWh"].sum().mean()
    weekend_ratio=div(weekend_daily,weekday_daily)*100
    daily=df.groupby("Date",as_index=False)["Electricity_kWh"].sum(); abnormal=daily[daily["Electricity_kWh"]>daily["Electricity_kWh"].mean()*1.2]
    peak=df.loc[df["Electricity_kWh"].idxmax()]; top=df.sort_values("Electricity_kWh",ascending=False).head(5)
    slope=None; r2=None
    if "Outdoor_Temperature" in df.columns:
        t=df.dropna(subset=["Outdoor_Temperature","Electricity_kWh"])
        if len(t)>12 and t["Outdoor_Temperature"].nunique()>3:
            x=t["Outdoor_Temperature"].to_numpy(); y=t["Electricity_kWh"].to_numpy(); slope,intercept=np.polyfit(x,y,1)
            pred=slope*x+intercept; ss_res=((y-pred)**2).sum(); ss_tot=((y-y.mean())**2).sum(); r2=1-ss_res/ss_tot if ss_tot>0 else 0
    avoid_night=max(0,night_avg-op_avg*.35)*len(df[df["IsNight"]]); night_save=avoid_night*unit
    avoid_week=max(0,weekend_daily-weekday_daily*.40)*df.loc[df["IsWeekend"],"Date"].nunique(); week_save=avoid_week*unit
    if slope is not None and slope>0 and "Outdoor_Temperature" in df.columns:
        cool_related=np.maximum(df["Outdoor_Temperature"]-26,0).sum()*slope; cool_low=cool_related*unit*.035; cool_high=cool_related*unit*.08
    else:
        cool_low=bill*.02; cool_high=bill*.05
    total_low=night_save+week_save+cool_low; total_high=night_save+week_save+cool_high
    score=100
    score-=24 if night_ratio>=55 else 16 if night_ratio>=45 else 8 if night_ratio>=35 else 0
    score-=22 if weekend_ratio>=60 else 15 if weekend_ratio>=50 else 8 if weekend_ratio>=40 else 0
    if slope is not None: score-=16 if slope>=5 else 9 if slope>=3 else 0
    score-=10 if len(abnormal)>=5 else 5 if len(abnormal)>=3 else 0
    score-=8 if div(total_low,bill)*100>=12 else 4 if div(total_low,bill)*100>=8 else 0
    score=max(0,min(100,round(score)))
    grade,label=("A","양호") if score>=80 else ("B","주의") if score>=65 else ("C","개선 필요") if score>=50 else ("D","우선 개선 필요")
    return {"df":df,"unit":unit,"op_avg":op_avg,"night_avg":night_avg,"night_ratio":night_ratio,"weekday_daily":weekday_daily,"weekend_daily":weekend_daily,"weekend_ratio":weekend_ratio,"daily":daily,"abnormal":abnormal,"peak":peak,"top":top,"slope":slope,"r2":r2,"avoid_night":avoid_night,"night_save":night_save,"avoid_week":avoid_week,"week_save":week_save,"cool_low":cool_low,"cool_high":cool_high,"total_low":total_low,"total_high":total_high,"score":score,"grade":grade,"label":label,"avg":df["Electricity_kWh"].mean(),"max":df["Electricity_kWh"].max(),"total":df["Electricity_kWh"].sum()}

def issue_summary(r):
    issues=[]
    if r["night_ratio"]>=45: issues.append("야간 기저부하 높음")
    if r["weekend_ratio"]>=50: issues.append("휴무일/주말 사용량 높음")
    if r["slope"] is not None and r["slope"]>=3: issues.append("냉방 민감도 높음")
    if len(r["abnormal"])>=3: issues.append("이상 사용일 다수")
    return issues or ["큰 이상 패턴 없음"]

def recs(r):
    rows=[]
    if r["night_ratio"]>=45: rows.append([1,"영업 종료 후 조명, 간판, 콘센트, 환기팬, 시스템에어컨 종료 상태 점검","높음","낮음"])
    elif r["night_ratio"]>=35: rows.append([1,"야간 대기전력과 공용부 전력 사용 점검","중간","낮음"])
    if r["weekend_ratio"]>=50: rows.append([len(rows)+1,"휴무일 냉방, 조명, 간판, 환기 스케줄 분리","높음","낮음"])
    elif r["weekend_ratio"]>=40: rows.append([len(rows)+1,"주말 운영 스케줄과 실제 설비 운전 상태 비교","중간","낮음"])
    if r["slope"] is not None and r["slope"]>=3: rows.append([len(rows)+1,"오후 피크 시간대 냉방 설정온도와 공간별 운전 스케줄 조정","중간~높음","중간"])
    rows.append([len(rows)+1,"피크 Top 5 시간대의 실제 설비 운전 상태 확인","중간","낮음"])
    rows.append([len(rows)+1,"층별 또는 주요 회로별 전력 계측 도입 검토","장기 효과","중간"])
    return pd.DataFrame(rows,columns=["우선순위","개선 조치","예상 효과","난이도"])

# ---------------- reports ----------------
def report_md(info,r,recdf):
    peak=r["peak"]; issues=', '.join(issue_summary(r))
    cool="외기온도 데이터가 없어 냉방 민감도는 계산하지 않았습니다." if r["slope"] is None else f"외기온도 1°C 상승 시 전력 사용량이 약 {r['slope']:.1f} kWh 증가하는 것으로 추정됩니다."
    rec_lines='\n'.join([f"{row['우선순위']}. {row['개선 조치']} | 예상 효과: {row['예상 효과']} | 난이도: {row['난이도']}" for _,row in recdf.iterrows()])
    return f"""# Wattda 월간 전기요금 진단 리포트

## 1. 요약 진단

**{info['building_name']}**의 전력 사용 패턴을 분석한 결과, 현재 진단 등급은 **{r['grade']}등급({r['label']})**, Wattda 점수는 **{r['score']}/100점**입니다.

주요 이슈는 **{issues}**입니다.

예상 월 절감 가능액은 **{krw(r['total_low'])}부터 {krw(r['total_high'])}**입니다. 연간 기준으로는 **{krw(r['total_low']*12)}부터 {krw(r['total_high']*12)}** 수준입니다.

---

## 2. 건물 기본정보

건물명: {info['building_name']}  
건물 용도: {info['building_type']}  
지역: {info['location']}  
연면적: {info['floor_area']:,}㎡  
운영 요일: {', '.join(info['operating_days'])}  
운영 시간: {info['operating_start'].strftime('%H:%M')}부터 {info['operating_end'].strftime('%H:%M')}  
월 전기요금: {krw(info['monthly_bill'])}  
월 전력사용량: {kwh(info['monthly_kwh'])}  
평균 전력 단가: {r['unit']:.1f}원/kWh  

---

## 3. 핵심 지표

총 분석 전력사용량: {kwh(r['total'])}  
평균 시간 사용량: {kwh(r['avg'])}  
최대 시간 사용량: {kwh(r['max'])}  
야간 평균 사용량: {kwh(r['night_avg'])}  
야간 사용 비율: {pct(r['night_ratio'])}  
주말 사용 비율: {pct(r['weekend_ratio'])}  
이상 사용일: {len(r['abnormal'])}일  

---

## 4. 피크 시간 분석

최대 전력 사용은 **{peak['DateTime'].strftime('%Y년 %m월 %d일 %H시')}**에 발생했습니다. 해당 시간의 전력 사용량은 **{peak['Electricity_kWh']:.1f} kWh**입니다.

---

## 5. 야간 기저부하 분석

야간 평균 사용량은 **{r['night_avg']:.1f} kWh/h**이며, 운영시간 평균 사용량의 **{r['night_ratio']:.1f}%** 수준입니다. 예상 비용 영향은 약 **{krw(r['night_save'])}**입니다.

---

## 6. 휴무일 및 주말 전력 사용 분석

주말 전력 사용량은 평일 평균 대비 **{r['weekend_ratio']:.1f}%** 수준입니다. 예상 비용 영향은 약 **{krw(r['week_save'])}**입니다.

---

## 7. 냉방 민감도 분석

{cool}

---

## 8. 예상 절감 가능액

야간 기저부하 절감 가능액: **{krw(r['night_save'])}**  
주말 및 휴무일 절감 가능액: **{krw(r['week_save'])}**  
냉방 스케줄 최적화 절감 가능액: **{krw(r['cool_low'])}부터 {krw(r['cool_high'])}**  
총 예상 월 절감 가능액: **{krw(r['total_low'])}부터 {krw(r['total_high'])}**  
총 예상 연간 절감 가능액: **{krw(r['total_low']*12)}부터 {krw(r['total_high']*12)}**

---

## 9. 우선 개선 조치

{rec_lines}

---

## 10. 다음 점검 항목

1. 영업 종료 30분 후 실제로 켜져 있는 설비를 현장에서 확인합니다.  
2. 간판, 공용부 조명, 환기팬, 시스템에어컨 종료 시간을 확인합니다.  
3. 휴무일 오전과 오후에 전력 사용 원인을 확인합니다.  
4. 피크 시간대에 실제 사용 공간과 냉방 운전 상태를 비교합니다.  
5. 조치 후 다음 달 Wattda 리포트에서 야간 사용량과 주말 사용률이 줄었는지 확인합니다.

---

## 11. 주의사항

이 리포트는 시간별 전력 데이터와 건물 기본정보를 기반으로 한 운영 진단용 추정 결과입니다. 실제 절감액은 설비 상태, 운영 방식, 요금제, 계절 조건에 따라 달라질 수 있습니다.
"""

def html_report(md):
    lines=[]
    for line in md.split('\n'):
        t=html.escape(line.strip()).replace('**','')
        if not t: continue
        if t.startswith('# '): lines.append(f'<h1>{t[2:]}</h1>')
        elif t.startswith('## '): lines.append(f'<h2>{t[3:]}</h2>')
        elif t.startswith('---'): lines.append('<hr>')
        else: lines.append(f'<p>{t}</p>')
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic",Arial,sans-serif;line-height:1.7;max-width:860px;margin:30px auto;padding:0 18px;color:#111827}h1{font-size:28px;border-bottom:3px solid #111827;padding-bottom:10px}h2{font-size:20px;margin-top:28px}hr{border:none;border-top:1px solid #e5e7eb;margin:24px 0}</style></head><body>'+''.join(lines)+'</body></html>'

def pdf_bytes(md):
    if not REPORTLAB_AVAILABLE: return None
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=34,leftMargin=34,topMargin=34,bottomMargin=34)
    font='Helvetica'
    for p in ['C:/Windows/Fonts/malgun.ttf','/usr/share/fonts/truetype/nanum/NanumGothic.ttf','/System/Library/Fonts/AppleSDGothicNeo.ttc']:
        if os.path.exists(p):
            try: pdfmetrics.registerFont(TTFont('KRFont',p)); font='KRFont'; break
            except Exception: pass
    styles=getSampleStyleSheet(); title=ParagraphStyle('t',parent=styles['Title'],fontName=font,fontSize=16,leading=22); h2=ParagraphStyle('h',parent=styles['Heading2'],fontName=font,fontSize=12,leading=16); body=ParagraphStyle('b',parent=styles['BodyText'],fontName=font,fontSize=9,leading=14)
    story=[]
    for line in md.split('\n'):
        t=html.escape(line.strip()).replace('**','')
        if not t: story.append(Spacer(1,4)); continue
        if t.startswith('# '): story.append(Paragraph(t[2:],title))
        elif t.startswith('## '): story.append(Paragraph(t[3:],h2))
        elif t.startswith('---'): story.append(Spacer(1,8))
        else: story.append(Paragraph(t,body))
    doc.build(story); buf.seek(0); return buf.getvalue()

# ---------------- state ----------------
default_info={"building_name":"Wattda 샘플 학원 A","building_type":"학원","location":"서울 강남구","floor_area":1200,"floors":5,"operating_days":["월","화","수","목","금","토"],"operating_start":time(13,0),"operating_end":time(22,0),"monthly_bill":3800000,"monthly_kwh":18500,"contract_power":80,"tariff_type":"일반용 전력 갑","cooling_type":"시스템에어컨"}
if 'info' not in st.session_state: st.session_state.info=default_info.copy()
if 'df' not in st.session_state: st.session_state.df=sample_data()
if 'result' not in st.session_state: st.session_state.result=analyze(st.session_state.df,st.session_state.info)
def refresh(): st.session_state.result=analyze(st.session_state.df,st.session_state.info)

# ---------------- UI ----------------
st.sidebar.title('⚡ Wattda'); st.sidebar.caption('전기요금 낭비 진단 AI')
page=st.sidebar.radio('메뉴',['홈','건물 정보','데이터 입력','진단 대시보드','리포트 생성','핸드폰/배포 안내'])
st.sidebar.divider(); st.sidebar.caption('현재 버전: Wattda MVP Final')
st.markdown('<div class="hero"><h1>⚡ Wattda</h1><p>전기요금 낭비, Wattda가 찾아드립니다.<br>중소형 건물의 전력 사용 데이터를 분석해 피크, 야간 기저부하, 휴무일 낭비, 냉방 민감도, 예상 절감액을 자동 리포트로 정리합니다.</p></div>',unsafe_allow_html=True)

if page=='홈':
    r=st.session_state.result; info=st.session_state.info
    c1,c2,c3,c4=st.columns(4); c1.metric('Wattda 점수',f"{r['score']}/100"); c2.metric('진단 등급',f"{r['grade']} | {r['label']}"); c3.metric('예상 월 절감액',f"{man(r['total_low'])} ~ {man(r['total_high'])}"); c4.metric('예상 연간 절감액',f"{man(r['total_low']*12)} ~ {man(r['total_high']*12)}")
    st.markdown('### 지금 이 MVP가 해주는 것')
    st.write('Wattda는 복잡한 BEMS 전체 시스템이 아니라, **전기요금 진단과 리포트 자동화**에 집중한 MVP입니다. 건물 정보와 시간별 전력 데이터를 넣으면 고객이 바로 이해할 수 있는 방식으로 문제와 절감 가능액을 보여줍니다.')
    a,b,c=st.columns(3)
    a.markdown('#### 1. 낭비 시간 탐지'); a.write('피크 시간, 야간 기저부하, 휴무일 사용량을 자동으로 찾아냅니다.')
    b.markdown('#### 2. 비용 환산'); b.write('kWh가 아니라 고객이 이해하기 쉬운 원 단위 절감액으로 바꿔줍니다.')
    c.markdown('#### 3. 리포트 생성'); c.write('고객 인터뷰와 영업에 바로 쓸 수 있는 한국어 리포트를 생성합니다.')
    st.info('다음 단계는 이 앱을 실제 고객 5명에게 보여주고, 리포트에 돈을 낼지 검증하는 것입니다.')

elif page=='건물 정보':
    st.subheader('건물 정보 입력'); info=st.session_state.info; col1,col2=st.columns(2)
    with col1:
        building_name=st.text_input('건물명',info['building_name']); types=['학원','스터디카페','피트니스센터','병원/의원','중소형 오피스','상가','기타']
        building_type=st.selectbox('건물 용도',types,index=types.index(info['building_type']) if info['building_type'] in types else 0)
        location=st.text_input('지역',info['location']); floor_area=st.number_input('연면적 ㎡',min_value=10,value=int(info['floor_area']),step=10); floors=st.number_input('층수',min_value=1,value=int(info['floors']),step=1)
    with col2:
        operating_days=st.multiselect('운영 요일',['월','화','수','목','금','토','일'],default=info['operating_days']); operating_start=st.time_input('운영 시작 시간',info['operating_start']); operating_end=st.time_input('운영 종료 시간',info['operating_end'])
        monthly_bill=st.number_input('월 전기요금 원',min_value=0,value=int(info['monthly_bill']),step=10000); monthly_kwh=st.number_input('월 전력사용량 kWh',min_value=1,value=int(info['monthly_kwh']),step=100); contract_power=st.number_input('계약전력 kW',min_value=1,value=int(info['contract_power']),step=1)
        tariff_type=st.selectbox('요금 종별',['일반용 전력 갑','일반용 전력 을','교육용','산업용','기타']); cooling_type=st.selectbox('냉방 방식',['시스템에어컨','개별 에어컨','중앙 냉방','냉방 없음','기타'])
    if st.button('저장하고 다시 분석',type='primary'):
        st.session_state.info={"building_name":building_name,"building_type":building_type,"location":location,"floor_area":floor_area,"floors":floors,"operating_days":operating_days,"operating_start":operating_start,"operating_end":operating_end,"monthly_bill":monthly_bill,"monthly_kwh":monthly_kwh,"contract_power":contract_power,"tariff_type":tariff_type,"cooling_type":cooling_type}; refresh(); st.success('저장 완료. 진단 결과가 갱신되었습니다.')
    st.caption('평균 단가는 월 전기요금 ÷ 월 전력사용량으로 계산합니다. 정밀 한전 요금제 계산은 추후 버전에서 추가하면 됩니다.')

elif page=='데이터 입력':
    st.subheader('전력 데이터 입력'); mode=st.radio('입력 방식',['샘플 데이터 사용','CSV 업로드'],horizontal=True)
    if mode=='샘플 데이터 사용':
        if st.button('샘플 데이터 초기화',type='primary'): st.session_state.df=sample_data(); refresh(); st.success('샘플 데이터가 적용되었습니다.')
    else:
        st.write('필수 컬럼: `DateTime`, `Electricity_kWh` / 선택 컬럼: `Outdoor_Temperature`')
        up=st.file_uploader('CSV 업로드',type=['csv'])
        if up is not None:
            try:
                df=pd.read_csv(up)
                if not {'DateTime','Electricity_kWh'}.issubset(df.columns): st.error('CSV에는 DateTime, Electricity_kWh 컬럼이 반드시 필요합니다.')
                else: st.session_state.df=prep(df); refresh(); st.success('CSV 업로드 완료. 진단 결과가 갱신되었습니다.')
            except Exception as e: st.error(f'CSV 처리 오류: {e}')
    st.markdown('### 현재 데이터 미리보기'); st.dataframe(st.session_state.df.head(80),width='stretch')
    st.download_button('현재 데이터 CSV 다운로드',data=st.session_state.df.to_csv(index=False).encode('utf-8-sig'),file_name='wattda_sample_data.csv',mime='text/csv')

elif page=='진단 대시보드':
    st.subheader('진단 대시보드'); r=st.session_state.result; df=r['df']; info=st.session_state.info
    c1,c2,c3,c4=st.columns(4); c1.metric('Wattda 점수',f"{r['score']}/100"); c2.metric('진단 등급',f"{r['grade']} | {r['label']}"); c3.metric('월 전기요금',krw(info['monthly_bill'])); c4.metric('평균 단가',f"{r['unit']:.1f}원/kWh")
    st.markdown('### 한눈에 보는 핵심 문제'); st.write(', '.join(issue_summary(r)))
    st.markdown('### 전력 사용 패턴'); st.line_chart(df.set_index('DateTime')[['Electricity_kWh']],height=300)
    st.markdown('### 핵심 진단 지표'); a,b,c=st.columns(3)
    a.metric('피크 시간',r['peak']['DateTime'].strftime('%m월 %d일 %H시')); a.metric('피크 사용량',kwh(r['peak']['Electricity_kWh']))
    b.metric('야간 평균 사용량',kwh(r['night_avg'])); b.metric('운영시간 대비 야간 비율',pct(r['night_ratio']))
    c.metric('주말 사용률',pct(r['weekend_ratio']));
    if r['slope'] is not None: c.metric('외기온도 1°C당 증가',f"{r['slope']:.1f} kWh")
    st.markdown('### 절감액 추정'); s1,s2,s3,s4=st.columns(4); s1.metric('야간 절감 가능액',krw(r['night_save'])); s2.metric('주말 절감 가능액',krw(r['week_save'])); s3.metric('냉방 최적화',f"{man(r['cool_low'])} ~ {man(r['cool_high'])}"); s4.metric('총 월 절감 가능액',f"{man(r['total_low'])} ~ {man(r['total_high'])}")
    st.markdown('### 피크 Top 5'); cols=['DateTime','Electricity_kWh']+(['Outdoor_Temperature'] if 'Outdoor_Temperature' in r['top'].columns else []); st.dataframe(r['top'][cols],width='stretch')
    st.markdown('### 개선안'); st.dataframe(recs(r),width='stretch')

elif page=='리포트 생성':
    st.subheader('리포트 생성'); info=st.session_state.info; r=st.session_state.result; recdf=recs(r); md=report_md(info,r,recdf)
    st.markdown('### 리포트 미리보기'); st.markdown(md); st.divider()
    st.download_button('Markdown 리포트 다운로드',data=md.encode('utf-8-sig'),file_name='wattda_report.md',mime='text/markdown')
    st.download_button('HTML 리포트 다운로드',data=html_report(md).encode('utf-8-sig'),file_name='wattda_report.html',mime='text/html')
    pdf=pdf_bytes(md)
    if pdf: st.download_button('PDF 리포트 다운로드',data=pdf,file_name='wattda_report.pdf',mime='application/pdf')
    else: st.warning('PDF 기능을 쓰려면 reportlab 설치가 필요합니다. 명령어: py -m pip install reportlab')
    st.info('고객에게 처음 보여줄 때는 PDF보다 HTML 리포트가 더 안전합니다. 모바일에서도 열기 쉽고 한글 깨짐 가능성이 낮습니다.')

else:
    st.subheader('핸드폰에서 보는 방법')
    st.markdown('''
### 방법 1. 같은 와이파이에서 핸드폰으로 보기
노트북에서 실행하면 터미널에 이런 주소가 뜹니다.

`Local URL: http://localhost:8501`  
`Network URL: http://192.168.x.x:8501`

핸드폰이 노트북과 **같은 와이파이**에 연결되어 있으면, 핸드폰 브라우저에서 `Network URL`을 입력하면 볼 수 있습니다. 단, 노트북이 켜져 있고 Streamlit이 실행 중이어야 합니다.

### 방법 2. 외부에서도 볼 수 있게 배포하기
가장 쉬운 방법은 **Streamlit Community Cloud**입니다.

필요한 파일은 보통 2개입니다.
1. `wattda_final_app.py`
2. `requirements.txt`

GitHub에 올린 뒤 Streamlit Community Cloud에서 연결하면 `https://...streamlit.app` 같은 주소가 생깁니다. 이 주소는 핸드폰, 태블릿, 다른 컴퓨터에서도 접속할 수 있습니다.

### 지금 추천
오늘은 먼저 방법 1로 핸드폰에서 확인하고, 화면이 괜찮으면 방법 2로 배포하세요.
''')

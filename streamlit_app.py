# app.py
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pandas as pd
import asyncio
from dateutil import relativedelta as datere
from data_fetch import get_investment_data, get_odds_data, get_race_info
from data_process import save_odds_data, save_investment_data, get_overall_investment
from visualization import print_bar_chart
from config import (
    VENUE_OPTIONS, RACE_NUMBERS, METHOD_LIST_WITH_QPL, METHOD_LIST_WITHOUT_QPL,
    METHOD_CH_WITH_QPL, METHOD_CH_WITHOUT_QPL, PRINT_LIST_WITH_QPL, PRINT_LIST_WITHOUT_QPL, BENCHMARK_DICT
)

st.set_page_config(page_title="Jockey Race", layout="wide")
st.title("Jockey Race 賽馬程式")

# 初始化 session state
if "odds_dict" not in st.session_state:
    st.session_state.odds_dict = {method: pd.DataFrame() for method in METHOD_LIST_WITH_QPL}
if "investment_dict" not in st.session_state:
    st.session_state.investment_dict = {method: pd.DataFrame() for method in METHOD_LIST_WITH_QPL}
if "overall_investment_dict" not in st.session_state:
    st.session_state.overall_investment_dict = {method: pd.DataFrame() for method in METHOD_LIST_WITH_QPL}
    st.session_state.overall_investment_dict["overall"] = pd.DataFrame()
if "race_dataframes" not in st.session_state:
    st.session_state.race_dataframes = {}
if "numbered_dict" not in st.session_state:
    st.session_state.numbered_dict = {}
if "post_time_dict" not in st.session_state:
    st.session_state.post_time_dict = {}

# 用戶輸入
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        Date = st.date_input("日期:", value=datetime.now())
    with col2:
        place = st.selectbox("場地:", VENUE_OPTIONS)
    with col3:
        race_no = st.selectbox("場次:", RACE_NUMBERS)
    no_qpl = st.checkbox("沒有位置Q", value=False)

# 根據 checkbox 設置 methodlist 和 print_list
methodlist = METHOD_LIST_WITHOUT_QPL if no_qpl else METHOD_LIST_WITH_QPL
methodCHlist = METHOD_CH_WITHOUT_QPL if no_qpl else METHOD_CH_WITH_QPL
print_list = PRINT_LIST_WITHOUT_QPL if no_qpl else PRINT_LIST_WITH_QPL

# 獲取賽事資訊
if st.button("開始"):
    st.session_state.reset = True
    race_dict, post_time_dict = asyncio.run(get_race_info(Date, place))
    st.session_state.post_time_dict = post_time_dict
    st.session_state.race_dataframes = {}
    st.session_state.numbered_dict = {}
    for race_number in race_dict:
        df = pd.DataFrame(race_dict[race_number])
        df.index += 1
        numbered_list = [f"{i+1}. {name}" for i, name in enumerate(race_dict[race_number]["馬名"])]
        st.session_state.numbered_dict[race_number] = numbered_list
        st.session_state.race_dataframes[race_number] = df

# 顯示賽事資訊
if st.session_state.get("reset", False):
    with st.container():
        st.write(f"DataFrame for Race No: {race_no}")
        st.dataframe(st.session_state.race_dataframes.get(race_no, pd.DataFrame()), use_container_width=True)

# 自動更新
st_autorefresh(interval=30000, key="data_refresh")
if st.session_state.get("reset", False):
    with st.container():
        time_now = datetime.now() + datere.relativedelta(hours=8)
        odds = asyncio.run(get_odds_data(Date, place, race_no, methodlist))
        investments = asyncio.run(get_investment_data(Date, place, race_no, methodlist))
        if odds and investments:
            save_odds_data(time_now, odds, st.session_state.odds_dict)
            save_investment_data(time_now, investments, odds, st.session_state.investment_dict)
            get_overall_investment(time_now, st.session_state.investment_dict, st.session_state.overall_investment_dict, methodlist)
            for method in print_list:
                print_bar_chart(
                    time_now, st.session_state.overall_investment_dict, st.session_state.odds_dict,
                    method, race_no, st.session_state.numbered_dict, st.session_state.post_time_dict
                )
        else:
            st.error("無法獲取數據，請檢查輸入或網路連線")

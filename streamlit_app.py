# app.py
import streamlit as st
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st.error("無法載入 streamlit_autorefresh 模組。請確保已安裝 streamlit-autorefresh (在 requirements.txt 中)。")
    st.stop()

import pandas as pd
from datetime import datetime, timedelta
from dateutil import relativedelta as datere
from data_fetch import get_investment_data, get_odds_data, get_race_info_sync
from data_process import save_odds_data, save_investment_data, get_overall_investment
from visualization import print_bar_chart
from config import (
    VENUE_OPTIONS, RACE_NUMBERS, METHOD_LIST_WITH_QPL, METHOD_LIST_WITHOUT_QPL,
    METHOD_CH_WITH_QPL, METHOD_CH_WITHOUT_QPL, PRINT_LIST_WITH_QPL, PRINT_LIST_WITHOUT_QPL, BENCHMARK_DICT
)

# 設置頁面配置
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
if "reset" not in st.session_state:
    st.session_state.reset = False
if "selected_race_no" not in st.session_state:
    st.session_state.selected_race_no = None

# 用戶輸入介面
with st.container():
    col1, col2 = st.columns(2)  # Adjusted to 2 columns since checkbox is removed
    with col1:
        Date = st.date_input("日期:", value=datetime.now())
    with col2:
        place = st.selectbox("場地:", VENUE_OPTIONS)

# 場次按鈕 (1-11) 排列為單行
with st.container():
    st.subheader("選擇場次")
    cols = st.columns(11)  # 11 columns for 11 buttons
    race_numbers = list(range(1, 12))  # 1 to 11
    for i, race_num in enumerate(race_numbers):
        cols[i].button(str(race_num), key=f"race_{race_num}", on_click=lambda x=race_num: st.session_state.update(selected_race_no=x))

# Set methodlist and print_list to default (with QPL)
methodlist = METHOD_LIST_WITH_QPL
methodCHlist = METHOD_CH_WITH_QPL
print_list = PRINT_LIST_WITH_QPL

# 獲取並優先顯示賽事資訊 (觸發於開始按鈕)
if st.button("開始"):
    st.session_state.reset = True
    try:
        race_dict, post_time_dict = get_race_info_sync(Date, place)
        st.session_state.post_time_dict = post_time_dict
        st.session_state.race_dataframes = {}
        st.session_state.numbered_dict = {}
        if not race_dict:
            st.warning(f"無賽事數據可用（日期: {Date}, 場地: {place}）。請檢查輸入或稍後重試。")
        else:
            for race_number in race_dict:
                df = pd.DataFrame(race_dict[race_number])
                df.index += 1
                numbered_list = [f"{i+1}. {name}" for i, name in enumerate(race_dict[race_number]["馬名"])]
                st.session_state.numbered_dict[race_number] = numbered_list
                st.session_state.race_dataframes[race_number] = df
    except Exception as e:
        st.error(f"無法獲取賽事資訊: {e}")
        st.session_state.reset = False

# 顯示選定場次的賽事資訊
race_no = st.session_state.selected_race_no
if race_no and st.session_state.get("reset", False):
    with st.container():
        st.subheader(f"場次 {race_no} 賽事資訊")
        if race_no in st.session_state.race_dataframes and not st.session_state.race_dataframes[race_no].empty:
            st.dataframe(
                st.session_state.race_dataframes[race_no],
                use_container_width=True,
                column_config={
                    "馬名": st.column_config.TextColumn("馬名", width="medium"),
                    "騎師": st.column_config.TextColumn("騎師", width="medium"),
                    "練馬師": st.column_config.TextColumn("練馬師", width="medium"),
                    "最近賽績": st.column_config.TextColumn("最近賽績", width="medium")
                }
            )
        else:
            st.warning(f"場次 {race_no} 無可用數據。請確認場次或稍後重試。")

# 自動更新賠率和投注數據 (觸發於選定場次)
if st.session_state.get("reset", False) and race_no:
    st_autorefresh(interval=60000, key="data_refresh")
    with st.container():
        st.subheader("賠率與投注數據")
        time_now = datetime.now() + datere.relativedelta(hours=8)
        try:
            odds = get_odds_data_sync(Date, place, race_no, methodlist)
            investments = get_investment_data_sync(Date, place, race_no, methodlist)
            if odds and investments:
                save_odds_data(time_now, odds, st.session_state.odds_dict)
                save_investment_data(time_now, investments, odds, st.session_state.investment_dict)
                get_overall_investment(time_now, st.session_state.investment_dict, st.session_state.overall_investment_dict, methodlist)
                for method in print_list:
                    st.write(f"{methodCHlist[methodlist.index(method)]} 圖表")
                    print_bar_chart(
                        time_now, st.session_state.overall_investment_dict, st.session_state.odds_dict,
                        method, race_no, st.session_state.numbered_dict, st.session_state.post_time_dict
                    )
            else:
                st.error("無法獲取賠率或投注數據，請檢查輸入或網路連線")
        except Exception as e:
            st.error(f"數據更新失敗: {e}")

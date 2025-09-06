# visualization.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
from datetime import timedelta
import logging

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from config import (
    VENUE_OPTIONS, RACE_NUMBERS, METHOD_LIST_WITH_QPL, METHOD_LIST_WITHOUT_QPL,
    METHOD_CH_WITH_QPL, METHOD_CH_WITHOUT_QPL, PRINT_LIST_WITH_QPL, PRINT_LIST_WITHOUT_QPL, BENCHMARK_DICT
)

def print_bar_chart(time_now, overall_investment_dict, odds_dict, method, race_no, numbered_dict, post_time_dict):
    # Check if post_time is available
    post_time = post_time_dict.get(race_no)
    if post_time is None:
        st.warning(f"場次 {race_no} 無截止時間數據")
        logging.warning(f"Post time is None for race {race_no}")
        return

    # Adjust post_time to HKT
    try:
        post_time_ts = pd.Timestamp(post_time) + timedelta(hours=8)
    except (ValueError, TypeError) as e:
        st.error(f"無法解析場次 {race_no} 的截止時間: {e}")
        logging.error(f"Failed to parse post_time for race {race_no}: {e}")
        return

    time_25_minutes_before = np.datetime64(post_time_ts - timedelta(minutes=25))
    time_5_minutes_before = np.datetime64(post_time_ts - timedelta(minutes=5))

    # Check if method is valid
    if method not in ["overall"] and method not in METHOD_LIST_WITH_QPL:
        logging.warning(f"Invalid method {method} for race {race_no}")
        return

    # Access data
    transformed_method = f"data_{method}"
    df = overall_investment_dict.get(transformed_method)
    if df is None or df.empty:
        st.warning(f"無數據可用於 {transformed_method} 圖表")
        logging.warning(f"No data or empty DataFrame for {transformed_method} in race {race_no}")
        return

    # Ensure 'time' column exists
    if 'time' not in df.columns:
        st.error(f"DataFrame for {transformed_method} missing 'time' column")
        logging.error(f"Missing 'time' column in {transformed_method} DataFrame for race {race_no}")
        return
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    if df['time'].isna().all():
        st.error(f"Invalid datetime values in 'time' column for {transformed_method}")
        logging.error(f"Invalid datetime values in 'time' column for {transformed_method} in race {race_no}")
        return

    # Filter data
    df_25 = df[df['time'] < time_25_minutes_before].tail(1)
    df_5 = df[df['time'] >= time_5_minutes_before].tail(1)

    if df_25.empty and df_5.empty:
        st.warning(f"無足夠數據生成 {method} 圖表")
        logging.warning(f"No data for 25min or 5min before post time for {method} in race {race_no}")
        return

    data_df = pd.concat([df_25, df_5]).reset_index(drop=True)
    if data_df.empty:
        st.warning(f"無有效數據生成 {method} 圖表")
        logging.warning(f"Concatenated DataFrame is empty for {method} in race {race_no}")
        return

    # Melt the DataFrame
    data_df = data_df.melt(id_vars=["time"], var_name="horse", value_name="investment")
    if data_df.empty:
        st.warning(f"無有效數據進行melt操作於 {method} 圖表")
        logging.warning(f"Melt operation resulted in empty DataFrame for {method} in race {race_no}")
        return

    data_df["time_label"] = data_df["time"].apply(
        lambda x: "25分鐘前" if x < time_25_minutes_before else "最近" if x >= time_5_minutes_before else "其他"
    )

    # Merge with odds if applicable
    if method in ["WIN", "PLA"]:
        odds_df = odds_dict.get(method)
        if odds_df is not None and not odds_df.empty:
            odds_df = odds_df.tail(1).melt(ignore_index=False).reset_index()
            odds_df.columns = ["time", "horse", "odds"]
            data_df = data_df.merge(odds_df[["horse", "odds"]], on="horse", how="left")
        else:
            st.warning(f"無賠率數據可用於 {method}")
            logging.warning(f"No odds data for {method} in race {race_no}")

    # Create chart
    chart = alt.Chart(data_df).mark_bar().encode(
        x=alt.X("horse:N", title="馬匹", sort=None),
        y=alt.Y("investment:Q", title="投注額", stack=None),
        color=alt.Color("time_label:N", title="時間"),
        tooltip=["horse", "investment", "time_label", "odds" if method in ["WIN", "PLA"] else None]
    ).properties(
        title=f"{method} 投注額",
        width=600,
        height=400
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

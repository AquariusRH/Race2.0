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

def print_bar_chart(
    time_now, overall_investment_dict, odds_dict, method, race_no,
    numbered_dict, post_time_dict, diff_dict=None
):
    # Get the cutoff/post time for the race
    post_time = post_time_dict.get(race_no)
    if post_time is None:
        st.warning(f"場次 {race_no} 無截止時間數據")
        return

    # Convert post_time to timezone-aware pd.Timestamp, add HKT offset
    try:
        post_time_ts = pd.Timestamp(post_time) + timedelta(hours=8)
    except Exception as e:
        st.error(f"截止時間解析錯誤: {e}")
        return

    # Calculate time window thresholds
    time_25_min_before = post_time_ts - timedelta(minutes=25)
    time_5_min_before = post_time_ts - timedelta(minutes=5)

    # Get relevant investment DataFrame
    df = overall_investment_dict.get(method)
    if df is None or df.empty:
        st.warning(f"{method} 無數據")
        return

    # Ensure index is datetime
    df.index = pd.to_datetime(df.index)

    # Time slicing by index
    df_1st = df[df.index < time_25_min_before].tail(1)
    df_2nd = df[df.index >= time_25_min_before].tail(1)
    df_3rd = df[df.index >= time_5_min_before].tail(1)

    # Prepare the time-labeled DataFrame
    if not df_1st.empty and not df_2nd.empty:
        data_df = pd.concat([df_1st, df_2nd])
        data_df['time_label'] = ['25分鐘前', '25分鐘後']
    elif not df_1st.empty:
        data_df = df_1st.copy()
        data_df['time_label'] = ['25分鐘前']
    elif not df_2nd.empty:
        data_df = df_2nd.copy()
        data_df['time_label'] = ['25分鐘後']
    else:
        st.warning(f"場次 {race_no} 無足夠分段數據")
        return

    # Add 'time' column from index for charting
    data_df = data_df.reset_index().rename(columns={'index': 'time'})

    # Melt DataFrame for Altair chart
    melt_cols = [c for c in data_df.columns if c not in ['time', 'time_label']]
    melt_df = data_df.melt(
        id_vars=['time', 'time_label'],
        value_vars=melt_cols,
        var_name='horse',
        value_name='investment'
    )

    # Merge odds data if applicable
    if method in ["WIN", "PLA"]:
        odds_df = odds_dict.get(method)
        if odds_df is not None and not odds_df.empty:
            odds_df = odds_df.tail(1).melt(ignore_index=False).reset_index()
            odds_df.columns = ["time", "horse", "odds"]
            melt_df = melt_df.merge(odds_df[["horse", "odds"]], on="horse", how="left")

    # Merge 'change' (改變) column if diff_dict provided
    if diff_dict is not None and method in diff_dict:
        if method == 'overall':
            change_data = diff_dict[method].iloc[-1]
        else:
            change_data = diff_dict[method].tail(10).sum(axis=0)
        change_df = pd.DataFrame(
            [change_data.apply(lambda x: x*4 if x > 0 else x*2)],
            columns=change_data.index
        )
        change_melt_df = change_df.melt(var_name="horse", value_name="change")
        melt_df = melt_df.merge(change_melt_df, on="horse", how="left")

    # Map numbered_dict labels for tooltips and x-axis
    melt_df['label'] = melt_df['horse'].apply(
        lambda i: numbered_dict[race_no][int(i)-1]
        if str(i).isdigit() and int(i) <= len(numbered_dict[race_no]) else str(i)
    )

    # Altair chart generation
    base = alt.Chart(melt_df).mark_bar().encode(
        x=alt.X("label:N", title="馬匹"),
        y=alt.Y("investment:Q", title="投注額"),
        color=alt.Color("time_label:N", title="時間"),
        tooltip=[
            "label", "investment",
            "odds" if method in ["WIN", "PLA"] else "investment",
            "change" if "change" in melt_df.columns else "investment"
        ]
    )

    # Overlay odds value on bars (WIN, PLA only)
    if method in ["WIN", "PLA"] and "odds" in melt_df.columns:
        text_odds = alt.Chart(melt_df).mark_text(
            dy=-10, color='black', size=12
        ).encode(
            x=alt.X("label:N"),
            y=alt.Y("investment:Q"),
            text=alt.Text("odds:N")
        )
        chart = base + text_odds
    else:
        chart = base

    # Configure chart title
    chart = chart.properties(
        width=600,
        height=400,
        title={
            "overall": "綜合",
            "WIN": "獨贏",
            "PLA": "位置",
            "QIN": "連贏",
            "QPL": "位置Q"
        }.get(method, method) + " 投注額"
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


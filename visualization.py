# visualization.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
from datetime import timedelta

def print_bar_chart(time_now, overall_investment_dict, odds_dict, method, race_no, numbered_dict, post_time_dict):
    post_time = post_time_dict[race_no]
    time_25_minutes_before = pd.to_datetime(post_time - timedelta(minutes=25))
    time_5_minutes_before = pd.to_datetime(post_time - timedelta(minutes=5))

    if method == "overall" or method in METHOD_LIST_WITH_QPL:
        df = overall_investment_dict[method]
    else:
        return

    df.index = pd.to_datetime(df.index)
    df_25 = df[df.index < time_25_minutes_before].tail(1)
    df_5 = df[df.index >= time_5_minutes_before].tail(1)

    data_df = pd.concat([df_25, df_5]).reset_index()
    data_df = data_df.melt(id_vars=["index"], var_name="horse", value_name="investment")
    data_df["time"] = data_df["index"].apply(lambda x: "25分鐘前" if x < time_25_minutes_before else "最近")

    if method in ["WIN", "PLA"]:
        odds_df = odds_dict[method].tail(1).melt(ignore_index=False).reset_index()
        odds_df.columns = ["time", "horse", "odds"]
        data_df = data_df.merge(odds_df[["horse", "odds"]], on="horse", how="left")

    chart = alt.Chart(data_df).mark_bar().encode(
        x=alt.X("horse:N", title="馬匹", sort=None),
        y=alt.Y("investment:Q", title="投注額"),
        color=alt.Color("time:N", title="時間"),
        tooltip=["horse", "investment", "time", "odds" if method in ["WIN", "PLA"] else None]
    ).properties(
        title=f"{method} 投注額",
        width=600,
        height=400
    )
    st.altair_chart(chart, use_container_width=True)

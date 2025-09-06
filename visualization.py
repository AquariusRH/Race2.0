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
    post_time = post_time_dict[race_no]
    time_25_minutes_before = np.datetime64(post_time - timedelta(minutes=25) + timedelta(hours=8))
    time_5_minutes_before = np.datetime64(post_time - timedelta(minutes=5) + timedelta(hours=8))
  
    for method in PRINT_LIST_WITH_QPL:
      odds_list = pd.DataFrame()
      df = pd.DataFrame()
      if method == 'overall':
          df = overall_investment_dict[method]
          change_data = diff_dict[method].iloc[-1]
      elif method in METHOD_LIST_WITH_QPL:
          df = overall_investment_dict[method]
          change_data = diff_dict[method].tail(10).sum(axis = 0)
          odds_list = odds_dict[method].tail(1)
      if df.tail(1).sum(axis=1)[0]==0:
        continue
      fig, ax1 = plt.subplots(figsize=(12, 6))
      df.index = pd.to_datetime(df.index)
      df_1st = pd.DataFrame()
      df_1st_2nd = pd.DataFrame()
      df_2nd = pd.DataFrame()
      #df_3rd = pd.DataFrame()
      df_1st = df[df.index< time_25_minutes_before].tail(1)
      df_1st_2nd = df[df.index >= time_25_minutes_before].head(1)
      df_2nd = df[df.index >= time_25_minutes_before].tail(1)
      df_3rd = df[df.index>= time_5_minutes_before].tail(1)

      change_df = pd.DataFrame([change_data.apply(lambda x: x*4 if x > 0 else x*2)],columns=change_data.index,index =[df.index[-1]])
      print(change_df)
      if method in ['WIN', 'PLA']:
        odds_list.index = pd.to_datetime(odds_list.index)
        odds_1st = odds_list[odds_list.index< time_25_minutes_before].tail(1)
        odds_2nd = odds_list[odds_list.index >= time_25_minutes_before].tail(1)
        #odds_3rd = odds_list[odds_list.index>= time_5_minutes_before].tail(1)

      bars_1st = None
      bars_2nd = None
      #bars_3rd = None
      # Initialize data_df
      if not df_1st.empty:
          data_df = df_1st
          data_df = data_df._append(df_2nd)
      elif not df_1st_2nd.empty:
          data_df = df_1st_2nd
          if not df_2nd.empty and not df_2nd.equals(df_1st_2nd):  # Avoid appending identical df_2nd
              data_df = data_df._append(df_2nd)
      else:
          data_df = pd.DataFrame()  # Fallback if both are empty
      #final_data_df = data_df._append(df_3rd)
      final_data_df = data_df
      sorted_final_data_df = final_data_df.sort_values(by=final_data_df.index[0], axis=1, ascending=False)
      diff = sorted_final_data_df.diff().dropna()
      diff[diff < 0] = 0
      X = sorted_final_data_df.columns
      X_axis = np.arange(len(X))
      sorted_change_df = change_df[X]
      if df_3rd.empty:
                  bar_colour = 'blue'
      else:
                  bar_colour = 'red'
      if not df_1st.empty:
          if df_2nd.empty:
                bars_1st = ax1.bar(X_axis, sorted_final_data_df.iloc[0], 0.4, label='投注額', color='pink')
          else:
                bars_2nd = ax1.bar(X_axis - 0.2, sorted_final_data_df.iloc[1], 0.4, label='25分鐘', color=bar_colour)
                bar = ax1.bar(X_axis+0.2,sorted_change_df.iloc[0],0.4,label='改變',color='grey')
                #if not df_3rd.empty:
                    #bars_3rd = ax1.bar(X_axis, diff.iloc[0], 0.3, label='5分鐘', color='red')
      else:
            if df_2nd.equals(df_1st_2nd):
              bars_2nd = ax1.bar(X_axis - 0.2, sorted_final_data_df.iloc[0], 0.4, label='25分鐘', color=bar_colour)
            else:
                bars_2nd = ax1.bar(X_axis - 0.2, sorted_final_data_df.iloc[1], 0.4, label='25分鐘', color=bar_colour)
                bar = ax1.bar(X_axis+0.2,sorted_change_df.iloc[0],0.4,label='改變',color='grey')
                #if not df_3rd.empty:
                    #bars_3rd = ax1.bar(X_axis, diff.iloc[0], 0.3, label='5分鐘', color='red')
            #else:
                #bars_3rd = ax1.bar(X_axis-0.2, sorted_final_data_df.iloc[0], 0.4, label='5分鐘', color='red')
                #bar = ax1.bar(X_axis+0.2,sorted_change_df.iloc[0],0.4,label='改變',color='grey')

      # Add numbers above bars
      if method in ['WIN', 'PLA']:
        if bars_2nd is not None:
          sorted_odds_list_2nd = odds_2nd[X].iloc[0]
          for bar, odds in zip(bars_2nd, sorted_odds_list_2nd):
              yval = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')
        #if bars_3rd is not None:
          #sorted_odds_list_3rd = odds_3rd[X].iloc[0]
          #for bar, odds in zip(bars_3rd, sorted_odds_list_3rd):
               # yval = bar.get_height()
                #ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')
        elif bars_1st is not None:
          sorted_odds_list_1st = odds_1st[X].iloc[0]
          for bar, odds in zip(bars_1st, sorted_odds_list_1st):
              yval = bar.get_height()
              ax1.text(bar.get_x() + bar.get_width() / 2, yval, odds, ha='center', va='bottom')

      namelist_sort = [numbered_dict[race_no][i - 1] for i in X]
      formatted_namelist = [label.split('.')[0] + '.' + '\n'.join(label.split('.')[1]) for label in namelist_sort]
      plt.xticks(X_axis, formatted_namelist, fontsize=12)
      ax1.grid(color='lightgrey', axis='y', linestyle='--')
      ax1.set_ylabel('投注額',fontsize=15)
      ax1.tick_params(axis='y')
      fig.legend()

      if method == 'overall':
          plt.title('綜合', fontsize=15)
      elif method == 'QIN':
          plt.title('連贏', fontsize=15)
      elif method == 'QPL':
          plt.title('位置Q', fontsize=15)
      elif method == 'WIN':
          plt.title('獨贏', fontsize=15)
      elif method == 'PLA':
          plt.title('位置', fontsize=15)
      st.pyplot(fig)


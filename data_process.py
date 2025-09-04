# data_process.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil import relativedelta as datere

def save_odds_data(time_now, odds, odds_dict):
    for method in odds:
        if method in ["WIN", "PLA"]:
            new_row = pd.DataFrame([odds[method]], index=[time_now], columns=np.arange(1, len(odds[method]) + 1))
        else:
            if odds[method]:
                combination, odds_array = zip(*odds[method])
                new_row = pd.DataFrame([odds_array], index=[time_now], columns=combination)
            else:
                continue
        odds_dict[method] = pd.concat([odds_dict[method], new_row])

def save_investment_data(time_now, investments, odds, investment_dict):
    for method in investments:
        if method in ["WIN", "PLA"]:
            investment_df = [round(investments[method][0] * 0.825 / 1000 / odd, 2) for odd in odds[method]]
            new_row = pd.DataFrame([investment_df], index=[time_now], columns=np.arange(1, len(odds[method]) + 1))
        else:
            if odds[method]:
                combination, odds_array = zip(*odds[method])
                investment_df = [round(investments[method][0] * 0.825 / 1000 / odd, 2) for odd in odds_array]
                new_row = pd.DataFrame([investment_df], index=[time_now], columns=combination)
            else:
                continue
        investment_dict[method] = pd.concat([investment_dict[method], new_row])

def get_overall_investment(time_now, investment_dict, overall_investment_dict, methodlist):
    no_of_horse = len(investment_dict["WIN"].columns)
    total_investment_df = pd.DataFrame(index=[time_now], columns=np.arange(1, no_of_horse + 1))
    for method in methodlist:
        if method in ["WIN", "PLA"]:
            overall_investment_dict[method] = pd.concat([overall_investment_dict[method], investment_dict[method].tail(1)])
        elif method in ["QIN", "QPL"]:
            combined = investment_combined(time_now, method, investment_dict[method].tail(1))
            overall_investment_dict[method] = pd.concat([overall_investment_dict[method], combined])
    for horse in range(1, no_of_horse + 1):
        total_investment = sum(
            overall_investment_dict[method][horse].iloc[-1] for method in methodlist if horse in overall_investment_dict[method].columns
        )
        total_investment_df[horse] = total_investment
    overall_investment_dict["overall"] = pd.concat([overall_investment_dict["overall"], total_investment_df])

def investment_combined(time_now, method, df):
    sums = {}
    for col in df.columns:
        num1, num2 = map(int, col.split(","))
        col_sum = df[col].sum()
        sums[num1] = sums.get(num1, 0) + col_sum
        sums[num2] = sums.get(num2, 0) + col_sum
    return pd.DataFrame([sums], index=[time_now]) / 2

# data_fetch.py
import aiohttp
import asyncio
import streamlit as st
import pandas as pd
import numpy as np
from config import API_URL, HEADERS, METHOD_LIST_WITH_QPL

async def fetch_data(url, payload, headers):
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        st.warning(f"API 請求失敗，狀態碼: {response.status}")
            except aiohttp.ClientError as e:
                st.error(f"請求錯誤: {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
    return None

@st.cache_data(ttl=60)
def get_investment_data_sync(_date, _place, _race_no, _methodlist):
    # Synchronous wrapper to run async function
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If running in Streamlit, use run_coroutine_threadsafe
        future = asyncio.run_coroutine_threadsafe(
            get_investment_data(_date, _place, _race_no, _methodlist), loop
        )
        return future.result()
    else:
        return asyncio.run(get_investment_data(_date, _place, _race_no, _methodlist))

async def get_investment_data(date, place, race_no, methodlist=METHOD_LIST_WITH_QPL):
    payload = {
        "operationName": "racing",
        "variables": {"date": str(date), "venueCode": place, "raceNo": int(race_no), "oddsTypes": methodlist},
        "query": """
        query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) {
            raceMeetings(date: $date, venueCode: $venueCode) {
                totalInvestment
                poolInvs: pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) {
                    id
                    leg { number races }
                    status
                    sellStatus
                    oddsType
                    investment
                    mergedPoolId
                    lastUpdateTime
                }
            }
        }
        """
    }
    data = await fetch_data(API_URL, payload, HEADERS)
    if not data:
        return None
    investments = {method: [] for method in methodlist}
    race_meetings = data.get("data", {}).get("raceMeetings", [])
    if race_meetings:
        for meeting in race_meetings:
            pool_invs = meeting.get("poolInvs", [])
            for pool in pool_invs:
                if place not in ["ST", "HV"]:
                    pool_id = pool.get("id")
                    if pool_id[8:10] != place:
                        continue
                investment = float(pool.get("investment"))
                investments[pool.get("oddsType")].append(investment)
    return investments

@st.cache_data(ttl=60)
def get_odds_data_sync(_date, _place, _race_no, _methodlist):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            get_odds_data(_date, _place, _race_no, _methodlist), loop
        )
        return future.result()
    else:
        return asyncio.run(get_odds_data(_date, _place, _race_no, _methodlist))

async def get_odds_data(date, place, race_no, methodlist=METHOD_LIST_WITH_QPL):
    payload = {
        "operationName": "racing",
        "variables": {"date": str(date), "venueCode": place, "raceNo": int(race_no), "oddsTypes": methodlist},
        "query": """
        query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) {
            raceMeetings(date: $date, venueCode: $venueCode) {
                pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) {
                    id
                    status
                    sellStatus
                    oddsType
                    lastUpdateTime
                    guarantee
                    minTicketCost
                    name_en
                    name_ch
                    leg { number races }
                    cWinSelections { composite name_ch name_en starters }
                    oddsNodes { combString oddsValue hotFavourite oddsDropValue bankerOdds { combString oddsValue } }
                }
            }
        }
        """
    }
    data = await fetch_data(API_URL, payload, HEADERS)
    if not data:
        return None
    odds_values = {method: [] for method in methodlist}
    race_meetings = data.get("data", {}).get("raceMeetings", [])
    for meeting in race_meetings:
        pm_pools = meeting.get("pmPools", [])
        for pool in pm_pools:
            if place not in ["ST", "HV"]:
                pool_id = pool.get("id")
                if pool_id[8:10] != place:
                    continue
            odds_nodes = pool.get("oddsNodes", [])
            odds_type = pool.get("oddsType")
            for node in odds_nodes:
                odds_value = node.get("oddsValue")
                odds_value = np.inf if odds_value == "SCR" else float(odds_value)
                if odds_type in ["QIN", "QPL", "FCT", "TRI", "FF"]:
                    odds_values[odds_type].append((node.get("combString"), odds_value))
                else:
                    odds_values[odds_type].append(odds_value)
        for odds_type in ["QIN", "QPL", "FCT", "TRI", "FF"]:
            odds_values[odds_type].sort(key=lambda x: x[0] if x else None)
    return odds_values

@st.cache_data(ttl=60)
def get_race_info_sync(_date, _place):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(get_race_info(_date, _place), loop)
        return future.result()
    else:
        return asyncio.run(get_race_info(_date, _place))

async def get_race_info(date, place):
    payload = {
        "operationName": "raceMeetings",
        "variables": {"date": str(date), "venueCode": place},
        "query": """
        query raceMeetings($date: String, $venueCode: String) {
            raceMeetings(date: $date, venueCode: $venueCode) {
                races {
                    no
                    postTime
                    runners {
                        id
                        no
                        standbyNo
                        name_ch
                        jockey { name_ch }
                        trainer { name_ch }
                        last6run
                    }
                }
            }
        }
        """
    }
    data = await fetch_data(API_URL, payload, HEADERS)
    if not data:
        return {}, {}
    race_dict = {}
    post_time_dict = {}
    race_meetings = data.get("data", {}).get("raceMeetings", [])
    for meeting in race_meetings:
        for race in meeting.get("races", []):
            race_number = race["no"]
            post_time = race.get("postTime")
            time_part = pd.to_datetime(post_time)
            post_time_dict[race_number] = time_part
            race_dict[race_number] = {"馬名": [], "騎師": [], "練馬師": [], "最近賽績": []}
            for runner in race.get("runners", []):
                if runner.get("standbyNo") == "":
                    race_dict[race_number]["馬名"].append(runner.get("name_ch", ""))
                    race_dict[race_number]["騎師"].append(runner.get("jockey", {}).get("name_ch", ""))
                    race_dict[race_number]["練馬師"].append(runner.get("trainer", {}).get("name_ch", ""))
                    race_dict[race_number]["最近賽績"].append(runner.get("last6run", ""))
    return race_dict, post_time_dict

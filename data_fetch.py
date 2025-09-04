# data_fetch.py
import requests
import aiohttp
import asyncio
import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from config import API_URL, HEADERS, METHOD_LIST_WITH_QPL

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@st.cache_data(ttl=60)
def get_race_info_sync(_date, _place):
    url = API_URL
    payload = {
        "operationName": "raceMeetings",
        "variables": {"date": str(_date), "venueCode": _place},
        "query": """
        fragment raceFragment on Race {
            id
            no
            status
            raceName_en
            raceName_ch
            postTime
            country_en
            country_ch
            distance
            wageringFieldSize
            go_en
            go_ch
            ratingType
            raceTrack { description_en description_ch }
            raceCourse { description_en description_ch displayCode }
            claCode
            raceClass_en
            raceClass_ch
            judgeSigns { value_en }
        }
        fragment racingBlockFragment on RaceMeeting {
            jpEsts: pmPools(oddsTypes: [TCE, TRI, FF, QTT, DT, TT, SixUP], filters: ["jackpot", "estimatedDividend"]) {
                leg { number races }
                oddsType
                jackpot
                estimatedDividend
                mergedPoolId
            }
            poolInvs: pmPools(oddsTypes: [WIN, PLA, QIN, QPL, CWA, CWB, CWC, IWN, FCT, TCE, TRI, FF, QTT, DBL, TBL, DT, TT, SixUP]) {
                id
                leg { races }
            }
            penetrometerReadings(filters: ["first"]) { reading readingTime }
            hammerReadings(filters: ["first"]) { reading readingTime }
            changeHistories(filters: ["top3"]) {
                type
                time
                raceNo
                runnerNo
                horseName_ch
                horseName_en
                jockeyName_ch
                jockeyName_en
                scratchHorseName_ch
                scratchHorseName_en
                handicapWeight
                scrResvIndicator
            }
        }
        query raceMeetings($date: String, $venueCode: String) {
            timeOffset { rc }
            activeMeetings: raceMeetings { id venueCode date status races { no postTime status wageringFieldSize } }
            raceMeetings(date: $date, venueCode: $venueCode) {
                id
                status
                venueCode
                date
                totalNumberOfRace
                currentNumberOfRace
                dateOfWeek
                meetingType
                totalInvestment
                country { code namech nameen seq }
                races { ...raceFragment
                    runners {
                        id
                        no
                        standbyNo
                        status
                        name_ch
                        name_en
                        horse { id code }
                        color
                        barrierDrawNumber
                        handicapWeight
                        currentWeight
                        currentRating
                        internationalRating
                        gearInfo
                        racingColorFileName
                        allowance
                        trainerPreference
                        last6run
                        saddleClothNo
                        trumpCard
                        priority
                        finalPosition
                        deadHeat
                        winOdds
                        jockey { code name_en name_ch }
                        trainer { code name_en name_ch }
                    }
                }
                obSt: pmPools(oddsTypes: [WIN, PLA]) { leg { races } oddsType comingleStatus }
                poolInvs: pmPools(oddsTypes: [WIN, PLA, QIN, QPL, CWA, CWB, CWC, IWN, FCT, TCE, TRI, FF, QTT, DBL, TBL, DT, TT, SixUP]) {
                    id
                    leg { number races }
                    status
                    sellStatus
                    oddsType
                    investment
                    mergedPoolId
                    lastUpdateTime
                }
                ...racingBlockFragment
                pmPools(oddsTypes: []) { id }
                jkcInstNo: foPools(oddsTypes: [JKC], filters: ["top"]) { instNo }
                tncInstNo: foPools(oddsTypes: [TNC], filters: ["top"]) { instNo }
            }
        }
        """
    }
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Race info API request successful: {url}, payload: {payload}")
            race_dict = {}
            post_time_dict = {}
            race_meetings = data.get('data', {}).get('raceMeetings', [])
            if not race_meetings:
                logging.warning(f"No race meetings found for date: {_date}, place: {_place}")
                return {}, {}
            for meeting in race_meetings:
                races = meeting.get('races', [])
                if not races:
                    logging.warning(f"No races found for date: {_date}, place: {_place}")
                    continue
                for race in races:
                    race_number = race.get("no")
                    if not race_number:
                        continue
                    # Validate place against runner ID
                    runners = race.get('runners', [])
                    if runners and _place not in ["ST", "HV"]:
                        runner_id = runners[0].get('id', '')
                        if runner_id and runner_id[8:10] != _place:
                            continue
                    post_time = race.get("postTime")
                    time_part = datetime.fromisoformat(post_time) if post_time else None
                    post_time_dict[race_number] = time_part
                    race_dict[race_number] = {"馬名": [], "騎師": [], "練馬師": [], "最近賽績": []}
                    if not runners:
                        logging.warning(f"No runners found for race {race_number}")
                        continue
                    for runner in runners:
                        if runner.get('standbyNo') == "":
                            race_dict[race_number]["馬名"].append(runner.get('name_ch', ''))
                            race_dict[race_number]["騎師"].append(runner.get('jockey', {}).get('name_ch', ''))
                            race_dict[race_number]["練馬師"].append(runner.get('trainer', {}).get('name_ch', ''))
                            race_dict[race_number]["最近賽績"].append(runner.get('last6run', ''))
            if not race_dict:
                logging.warning(f"No valid race data constructed for date: {_date}, place: {_place}")
            return race_dict, post_time_dict
        else:
            logging.error(f"Race info API request failed, status code: {response.status_code}")
            st.error(f"賽事資訊 API 請求失敗，狀態碼: {response.status_code}")
            return {}, {}
    except Exception as e:
        logging.error(f"Error in get_race_info_sync: {e}")
        st.error(f"無法獲取賽事資訊: {e}")
        return {}, {}

async def fetch_data(url, payload, headers):
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logging.info(f"API request successful: {url}, payload: {payload}")
                        return data
                    else:
                        logging.warning(f"API request failed, status code: {response.status}")
                        st.warning(f"API 請求失敗，狀態碼: {response.status}")
            except aiohttp.ClientError as e:
                logging.error(f"API request error: {e}")
                st.error(f"請求錯誤: {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
    logging.error(f"API request failed after 3 attempts: {url}")
    return None

@st.cache_data(ttl=60)
def get_investment_data_sync(_date, _place, _race_no, _methodlist):
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
    if not data or not data.get("data", {}).get("raceMeetings"):
        logging.error(f"No valid investment data for date: {date}, place: {place}, race_no: {race_no}")
        return None
    investments = {method: [] for method in methodlist}
    race_meetings = data.get("data", {}).get("raceMeetings", [])
    for meeting in race_meetings:
        pool_invs = meeting.get("poolInvs", [])
        for pool in pool_invs:
            if place not in ["ST", "HV"]:
                pool_id = pool.get("id")
                if pool_id and pool_id[8:10] != place:
                    continue
            investment = float(pool.get("investment", 0))
            investments[pool.get("oddsType")].append(investment)
    return investments

@st.cache_data(ttl=60)
def get_odds_data_sync(_date, _place, _race_no, _methodlist):
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
    if not data or not data.get("data", {}).get("raceMeetings"):
        logging.error(f"No valid odds data for date: {date}, place: {place}, race_no: {race_no}")
        return None
    odds_values = {method: [] for method in methodlist}
    race_meetings = data.get("data", {}).get("raceMeetings", [])
    for meeting in race_meetings:
        pm_pools = meeting.get("pmPools", [])
        for pool in pm_pools:
            if place not in ["ST", "HV"]:
                pool_id = pool.get("id")
                if pool_id and pool_id[8:10] != place:
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

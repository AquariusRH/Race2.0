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

# data_fetch.py
import requests
import numpy as np
import pandas as pd
import streamlit as st
import logging
from datetime import datetime

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_investment_data(Date, place, race_no, methodlist):
    url = 'https://info.cld.hkjc.com/graphql/base/'
    headers = {'Content-Type': 'application/json'}
    payload_investment = {
        "operationName": "racing",
        "variables": {
            "date": str(Date),
            "venueCode": place,
            "raceNo": int(race_no),
            "oddsTypes": methodlist
        },
        "query": """
        query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) {
          raceMeetings(date: $date, venueCode: $venueCode) {
            totalInvestment
            poolInvs: pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) {
              id
              leg {
                number
                races
              }
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
    response = requests.post(url, headers=headers, json=payload_investment)
    if response.status_code == 200:
        investment_data = response.json()
        investments = {
            "WIN": [],
            "PLA": [],
            "QIN": [],
            "QPL": [],
            "FCT": [],
            "TRI": [],
            "FF": []
        }
        race_meetings = investment_data.get('data', {}).get('raceMeetings', [])
        if race_meetings:
            for meeting in race_meetings:
                pool_invs = meeting.get('poolInvs', [])
                for pool in pool_invs:
                    if place not in ['ST', 'HV']:
                        id = pool.get('id')
                        if id and id[8:10] != place:
                            continue
                    investment = float(pool.get('investment', 0))
                    odds_type = pool.get('oddsType')
                    if odds_type in investments:
                        investments[odds_type].append(investment)
            logging.info(f"Investment data fetched for race {race_no}: {investments.keys()}")
        else:
            logging.warning(f"No race meetings found in investment data for race {race_no}")
        return investments
    else:
        logging.error(f"Error fetching investment data for race {race_no}: {response.status_code}")
        return {method: [] for method in ["WIN", "PLA", "QIN", "QPL", "FCT", "TRI", "FF"]}

def get_odds_data(Date, place, race_no, methodlist):
    url = 'https://info.cld.hkjc.com/graphql/base/'
    headers = {'Content-Type': 'application/json'}
    payload_odds = {
        "operationName": "racing",
        "variables": {
            "date": str(Date),
            "venueCode": place,
            "raceNo": int(race_no),
            "oddsTypes": methodlist
        },
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
              leg {
                number
                races
              }
              cWinSelections {
                composite
                name_ch
                name_en
                starters
              }
              oddsNodes {
                combString
                oddsValue
                hotFavourite
                oddsDropValue
                bankerOdds {
                  combString
                  oddsValue
                }
              }
            }
          }
        }
        """
    }
    response = requests.post(url, headers=headers, json=payload_odds)
    if response.status_code == 200:
        odds_data = response.json()
        odds_values = {
            "WIN": [],
            "PLA": [],
            "QIN": [],
            "QPL": [],
            "FCT": [],
            "TRI": [],
            "FF": []
        }
        race_meetings = odds_data.get('data', {}).get('raceMeetings', [])
        for meeting in race_meetings:
            pm_pools = meeting.get('pmPools', [])
            for pool in pm_pools:
                if place not in ['ST', 'HV']:
                    id = pool.get('id')
                    if id and id[8:10] != place:
                        continue
                odds_nodes = pool.get('oddsNodes', [])
                odds_type = pool.get('oddsType')
                if not odds_type or odds_type not in odds_values:
                    continue
                odds_values[odds_type] = []
                for node in odds_nodes:
                    odds_value = node.get('oddsValue')
                    if odds_value == 'SCR':
                        odds_value = np.inf
                    else:
                        try:
                            odds_value = float(odds_value)
                        except (ValueError, TypeError):
                            continue
                    comb_string = node.get('combString')
                    if odds_type in ["QIN", "QPL", "FCT", "TRI", "FF"] and comb_string:
                        odds_values[odds_type].append((comb_string, odds_value))
                    else:
                        odds_values[odds_type].append(odds_value)
                for odds_type in ["QIN", "QPL", "FCT", "TRI", "FF"]:
                    odds_values[odds_type].sort(key=lambda x: x[0], reverse=False)
        logging.info(f"Odds data fetched for race {race_no}: {odds_values.keys()}")
        return odds_values
    else:
        logging.error(f"Error fetching odds data for race {race_no}: {response.status_code}")
        return {method: [] for method in ["WIN", "PLA", "QIN", "QPL", "FCT", "TRI", "FF"]}

# Existing get_race_info_sync remains unchanged

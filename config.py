# config.py
API_URL = "https://info.cld.hkjc.com/graphql/base/"
HEADERS = {"Content-Type": "application/json"}

# 場地選項
VENUE_OPTIONS = ["ST", "HV", "S1", "S2", "S3", "S4", "S5"]
RACE_NUMBERS = list(range(1, 12))

# 投注類型
METHOD_LIST_WITH_QPL = ["WIN", "PLA", "QIN", "QPL", "FCT", "TRI", "FF"]
METHOD_LIST_WITHOUT_QPL = ["WIN", "PLA", "QIN", "TRI"]
METHOD_CH_WITH_QPL = ["獨贏", "位置", "連贏", "位置Q", "二重彩", "單T", "四連環"]
METHOD_CH_WITHOUT_QPL = ["獨贏", "位置", "連贏", "單T"]
PRINT_LIST_WITH_QPL = ["qin_qpl", "PLA", "WIN"]
PRINT_LIST_WITHOUT_QPL = ["qin", "PLA", "WIN"]

# 基準值
BENCHMARK_DICT = {
    "WIN": 10,
    "PLA": 100,
    "QIN": 50,
    "QPL": 100
}

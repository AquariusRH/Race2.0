import requests
from bs4 import BeautifulSoup

# 設定賽事資訊
race_date = "2025/05/14"
racecourse = "HV"
race_no = "1"

# 構建 URL 和參數
url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalOdds.aspx"
params = {
    "RaceDate": race_date,
    "Racecourse": racecourse,
    "RaceNo": race_no
}

# 設定 headers
headers = {
    "User-Agent": "Mozilla/5.0"
}

# 發送 GET 請求
response = requests.get(url, params=params, headers=headers)
response.encoding = "utf-8"  # 設定正確的編碼

# 解析 HTML
soup = BeautifulSoup(response.text, "html.parser")

# 找到賠率表格
table = soup.find("table", class_="table_bd")
if table:
    rows = table.find_all("tr")
    for row in rows:
        cols = [col.text.strip() for col in row.find_all("td")]
        if cols:
            print(cols)
else:
    print("未找到賠率資料")

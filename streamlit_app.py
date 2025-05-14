import requests
from bs4 import BeautifulSoup

url = "https://racing.hkjc.com/racing/information/Chinese/Racing/LocalResults.aspx"
params = {
    "RaceDate": "2024/05/12",
    "Racecourse": "ST",
    "RaceNo": "10"
}

headers = {
    "User-Agent": "Mozilla/5.0",
}

res = requests.get(url, params=params, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

# 找到賽馬成績表格
table = soup.find("table", class_="table_bd")
rows = table.find_all("tr")

for row in rows:
    cols = [col.text.strip() for col in row.find_all("td")]
    print(cols)

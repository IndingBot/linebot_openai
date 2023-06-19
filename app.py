from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# # OPENAI API Key初始化設定
# openai.api_key = os.getenv('OPENAI_API_KEY')

def getTest(car_no):
  import re
  import requests
  from bs4 import BeautifulSoup
  import pandas as pd
  from datetime import datetime
  from lxml import html

  today = datetime.today().strftime('%Y-%m-%d')
  # car_no = "aaa100" #@param {type:"string"}
  url = f"https://mobile.epa.gov.tw/Motor/query/Query_Check_Print.aspx?Car_No={car_no}"
  response = requests.get(url)
  response.encoding = "utf8"
  soup = BeautifulSoup(response.text, "html.parser")
  data = soup.find_all('table')
  df = pd.read_html(str(data))[2]
  df = df[df['檢驗別']=='定期檢驗']
  lastTest = datetime.strptime(str(df['檢測日期'][0]), '%Y%m%d').strftime('%Y-%m-%d')
  df = pd.read_html(str(data))[3]
  outdate = df['出廠日'][0]
  tree = html.fromstring(response.content)
  t = tree.xpath('//*[@id="lblTestStatus"]/center/font/text()')[0]

  text = soup.find('span', {'id': 'lblTestYearMonth'}).text
  m = int(re.findall(r'\d+月', text)[0].replace('月',''))
  y = int(re.findall(r'\d+年', text)[0].replace('年',''))
  now_y = datetime.now().year
  y = now_y  if now_y >= y else y
  date = '%4d%02d01'% (y,m)
  text = text.replace('註：您',car_no).replace(" ","")
  status = soup.find('span', {'id': 'lblTestStatus'}).text
  TestYearMonth = soup.find('span', {'id': 'lblTestYearMonth'}).text
  TestYearMonth = TestYearMonth.replace('註：您','')
  return status

def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    t = getTest(msg)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(t))

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import requests
import sys
import json
import os
from datetime import datetime
from time import sleep
import iksm

VERSION = "1.5.0"
LANG = "en-US"


class SalmonRec():
    def __init__(self):
        print(datetime.now().strftime("%H:%M:%S ") + "Salmonia version b3")
        print(datetime.now().strftime("%H:%M:%S ") + "Thanks @Yukinkling and @barley_ural!")
        path = os.path.dirname(os.path.abspath(sys.argv[0])) + "/config.json"
        try:
            with open(path) as f:
                df = json.load(f)
                self.cookie = df["iksm_session"]
                self.session = df["session_token"]
                self.token = df["api-token"]
                self.latest = df["latest"]
        except FileNotFoundError:
            print(datetime.now().strftime("%H:%M:%S ") + "config.json is not found.")
            self.setConfig()

        url = "https://app.splatoon2.nintendo.net"
        print(datetime.now().strftime("%H:%M:%S ") + "Checking iksm_session's validation.")
        res = requests.get(url, cookies=dict(iksm_session=self.cookie))
        if res.status_code == 200:
            print(datetime.now().strftime("%H:%M:%S ") + "Your iksm_session is valid.")
        if res.status_code == 403:
            if res.text == "Forbidden":
                print(datetime.now().strftime("%H:%M:%S ") + "Your iksm_session is expired.")
                if self.session != "":
                    print(datetime.now().strftime("%H:%M:%S ") + "Regenerate iksm_session.")
                    # Regenerate iksm_session with session_token
                    self.cookie = iksm.get_cookie(self.session, LANG, VERSION)
                    with open("config.json", mode="w") as f:
                        data = {
                            "iksm_session": self.cookie,
                            "session_token": self.session,
                            "api-token": self.token,
                            "latest": self.latest,
                        }
                        json.dump(data, f, indent=4)
                else:
                    self.setConfig()
            else:
                print(datetime.now().strftime("%H:%M:%S ") + "Unknown error.")
                sys.exit()

    def setConfig(self, token=""):
        self.session = iksm.log_in(VERSION)
        self.cookie = iksm.get_cookie(self.session, LANG, VERSION)
        with open("config.json", mode="w") as f:
            data = {
                "iksm_session": self.cookie,
                "session_token": self.session,
                "api-token": token,
                "latest": 0,
            }
            json.dump(data, f, indent=4)
        self.token = token
        self.latest = 0

    def upload(self, resid):
        resid = str(resid)
        path = "json/" + resid + ".json"
        file = json.load(open(path, "r"))
        result = {"results": [file]}
        url = "https://salmon-stats-api.yuki.games/api/results"
        headers = {"Content-type": "application/json",
                   "Authorization": "Bearer " + self.token}
        res = requests.post(url, data=json.dumps(result), headers=headers)

        if res.status_code == 401:  # 認証エラー
            print("Api token is invalid.")
            sys.exit()
        if res.status_code == 200:  # 認証成功
            # レスポンスの変換
            text = json.loads(res.text)[0]
            if text["created"] == False:
                print(datetime.now().strftime("%H:%M:%S ") + resid + " already uploaded!")
            else:
                print(datetime.now().strftime("%H:%M:%S ") + resid + " uploaded!")
        if res.status_code == 500:
            print(datetime.now().strftime("%H:%M:%S ") + resid + " is not recoginized schedule_id")


    def uploadAll(self):
        file = []
        dir = os.listdir("json")
        # ファイル名をソーティング
        for p in dir:
            file.append(p[0:-5])
        file.sort(key=int)

        for resid in file:
            if self.latest < int(resid):
                self.upload(resid)
                with open("config.json", mode="w") as f:
                    data = {
                        "iksm_session": self.cookie,
                        "session_token": self.session,
                        "api-token": self.token,
                        "latest": int(resid),
                    }
                    json.dump(data, f, indent=4)
            sleep(5)
        

    def getResults(self):
        # 最新のリザルトIDを取得する
        url = "https://app.splatoon2.nintendo.net/api/coop_results"
        res = requests.get(url, cookies=dict(iksm_session=self.cookie)).json()
        resmid = int(res["summary"]["card"]["job_num"])
        max = 50 if resmid >= 50 else resmid

        dir = os.listdir()
        if "json" not in dir: # ディレクトリがなければ作成
            print(datetime.now().strftime("%H:%M:%S ") + "Make directory...")
            os.mkdir("json")
        list = os.listdir("json")
        for i in range(1, max + 1):
            resid = resmid - max + i
            if (str(resid) + ".json") in list:
                continue
            print(datetime.now().strftime("%H:%M:%S ") +
                  "Saved " + str(resid))
            url = "https://app.splatoon2.nintendo.net/api/coop_results/" + \
                str(resid)
            res = requests.get(url, cookies=dict(
                iksm_session=self.cookie)).text
            path = os.path.dirname(os.path.abspath(
                sys.argv[0])) + "/json/" + str(resid) + ".json"
            with open(path, mode="w") as f:
                f.write(res)
            # トークンが保存されていたらアップロードする
            if self.token is not "":
                self.upload(resid)
            sleep(1)


if __name__ == "__main__":
    user = SalmonRec()

    # 保存済みデータのアップロード
    if user.token is not "":
        print(datetime.now().strftime("%H:%M:%S ") + "Checking your records.")
        user.uploadAll()

    print(datetime.now().strftime("%H:%M:%S ") + "Waiting new records.")

    while True:
        # 最新データを取得した上で、取得した最古のリザルトIDを保存
        user.getResults()
        sleep(10)

import requests
import sys
import json
import os
from datetime import datetime
from time import sleep

class SalmonRec():
    def __init__(self):
        print("Salmonia version b1")
        print("Thanks @Yukinkling and @barley_ural!")
        path = os.path.dirname(os.path.abspath(sys.argv[0])) + "/config.json"
        try:
            with open(path) as f:
                df = json.load(f)
                self.session = df["iksm_session"]
                self.token = df["api-token"]
                self.latest = df["latest"]
        except FileNotFoundError:
            print("config.json is not found.")
            sys.exit()

        url = "https://app.splatoon2.nintendo.net"
        print("Checking iksm_session's validation.")
        res = requests.get(url, cookies=dict(iksm_session=self.session))
        if res.status_code == 200:
            print("Your iksm_session is valid.")
        if res.status_code == 403:
            if res.text == "Forbidden":
                print("Your iksm_session is invalid.")
            else:
                print("Unknown error.")
            sys.exit()

    def upload(self, path, jobid):
        file = json.load(open(path, "r"))
        result = {"results": [file]}
        url = "https://salmon-stats-api.yuki.games/api/results"
        headers = {"Content-type": "application/json",
                   "Authorization": "Bearer " + self.token}
        res = requests.post(url, data=json.dumps(result), headers=headers)
        
        if res.status_code == 401: #認証エラー
            print("Api token is invalid.")
            sys.exit()
        if res.status_code == 200: #認証成功
            return True
        return False

    def uploadAll(self, latest):
        file = []
        dir = os.listdir("json")
        # ファイル名をソーティング
        for p in dir:
            file.append(p[0:-5])
        file.sort(key=int, reverse=True)
        
        # jobidでアップロード
        for jobid in file:
            # 設定ファイルから読み込んだ最新リザルトIDを使用
            if self.latest >= int(jobid):
                print(datetime.now().strftime('%Y/%m/%d %H:%M:%S') + " : No new records.")
                break
            path = "json/" + jobid + ".json"
            if self.upload(path, jobid) == True:
                print(datetime.now().strftime('%Y/%m/%d %H:%M:%S') + " : " + jobid + " uploaded success!")
            sleep(1)
            
        # 最新リザルトIDを更新
        self.latest = latest
        path = os.path.dirname(os.path.abspath(sys.argv[0])) + "/config.json"
        with open(path, "w") as f:
            config = {"iksm_session" : self.session, "api-token" : self.token, "latest" : self.latest}
            json.dump(config, f, indent=4)

    def getResults(self):
        # 最新のリザルトIDを取得する
        url = "https://app.splatoon2.nintendo.net/api/coop_results"
        res = requests.get(url, cookies=dict(iksm_session=self.session)).json()
        resid = int(res["summary"]["card"]["job_num"])
        max = 50 if resid >= 50 else resid

        dir = os.listdir()
        if "json" not in dir:
            print("Make Directory...")
            os.mkdir("json")
        list = os.listdir("json")
        for i in range(0, max):
            if (str(resid - i) + ".json") in list:
                break
            print(datetime.now().strftime('%Y/%m/%d %H:%M:%S') + " : Saving " + str(resid - i) + " ...")
            url = "https://app.splatoon2.nintendo.net/api/coop_results/" + \
                str(resid - i)
            res = requests.get(url, cookies=dict(iksm_session=self.session)).text
            path = os.path.dirname(os.path.abspath(
                sys.argv[0])) + "/json/" + str(resid - i) + ".json"
            with open(path, mode="w") as f:
                f.write(res)
            sleep(5)
        return resid

if __name__ == "__main__":
    user = SalmonRec()
    
    while True:
        # 最新データを取得した上で、取得した最新のリザルトIDを保存
        latest = user.getResults()
        user.uploadAll(latest)
        sleep(10)
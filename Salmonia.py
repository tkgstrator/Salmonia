import requests
import sys
import json
import os
from datetime import datetime
from time import sleep

class SalmonRec():
    def __init__(self):
        path = os.path.dirname(os.path.abspath(sys.argv[0])) + "/config.ini"
        try:
            with open(path) as f:
                self.session = f.readline().strip()
                self.token = f.readline().strip()
        except FileNotFoundError:
            print("config.ini is not found.")
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

    def upload(self, path):
        file = json.load(open(path, "r"))
        result = {"results": [file]}
        url = "https://salmon-stats-api.yuki.games/api/results"
        headers = {"Content-type": "application/json",
                   "Authorization": "Bearer " + self.token}
        res = requests.post(url, data=json.dumps(result), headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data[0]["created"] == True:
                return True
            else:
                return False
        else:
            return False

    def uploadAll(self):
        file = []
        dir = os.listdir("json")
        for p in dir:
            file.append(p[0:-5])
        file.sort(key=int, reverse=True)
        for p in file:
            base = p + ".json"
            if self.upload("json/" + base) == True:
                print(datetime.now().strftime('%Y/%m/%d %H:%M:%S') + " : " + base + " uploaded success!")
            else:
                print(datetime.now().strftime('%Y/%m/%d %H:%M:%S') + " : No new records.")
                return False
            sleep(10)
        return True

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
        return 0

if __name__ == "__main__":
    user = SalmonRec()
    
    while True:
        user.getResults()
        user.uploadAll()
        sleep(10)
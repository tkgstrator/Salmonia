# -*- coding: utf-8 -*-
import requests
import sys
import json
import os
import webbrowser
from datetime import datetime
from time import sleep
import iksm

VERSION = "1.5.2"
LANG = "en-US"
URL = "https://salmon-stats.yuki.games/"

class Param():
    def __init__(self):
        self.splatnet2 = 0
        self.local = 0

    def setup(self, iksm_session, session_token, api_token, salmonstats=0):
        self.iksm_session = iksm_session
        self.session_token = session_token
        self.api_token = api_token
        self.salmonstats = salmonstats

    def output(self):
        with open("config.json", mode="w") as f:
            data = {
                "iksm_session": self.iksm_session,
                "session_token": self.session_token,
                "api-token": self.api_token,
                "job_id": {
                    "splatnet2": self.splatnet2,
                    "salmonstats": self.salmonstats,
                    "local": self.local,
                }
            }
            json.dump(data, f, indent=4)

class SalmonRec():
    def __init__(self): # Initialize
        print(datetime.now().strftime("%H:%M:%S ") + "Salmonia version 1.0.4")
        print(datetime.now().strftime("%H:%M:%S ") + "Thanks @Yukinkling and @barley_ural!")
        print(datetime.now().strftime("%H:%M:%S ") + "Thank you for users")
        path = os.path.dirname(os.path.abspath(sys.argv[0])) + "/config.json"
        self.param = Param() # Setup Parameters
        
        try:
            with open(path) as f: # Exist
                try:
                    df = json.load(f)
                    self.param.setup(df["iksm_session"], df["session_token"], df["api-token"], df["job_id"]["salmonstats"])
                except json.decoder.JSONDecodeError:
                    print(datetime.now().strftime("%H:%M:%S ") + "config.json is broken.")
                    print(datetime.now().strftime("%H:%M:%S ") + "Regenerate config.json.")
        except FileNotFoundError: # None
            print(datetime.now().strftime("%H:%M:%S ") + "config.json is not found.")
            self.setConfig()
        
        dir = os.listdir() # Directory Checking
        if "json" not in dir: 
            print(datetime.now().strftime("%H:%M:%S ") + "Make directory...")
            os.mkdir("json")
        else:
            file = []
            dir = os.listdir("json")
            for p in dir:
                file.append(p[0:-5])
            file.sort(key=int, reverse=True)
            try:
                self.param.local = int(file[0]) # Latest Job_Id on Local
            except IndexError:
                self.param.local = 0

        # Checking iksm_session Validation
        url = "https://app.splatoon2.nintendo.net"
        print(datetime.now().strftime("%H:%M:%S ") + "Checking iksm_session's validation.")
        res = requests.get(url, cookies=dict(iksm_session=self.param.iksm_session))
        if res.status_code == 200:
            print(datetime.now().strftime("%H:%M:%S ") + "Your iksm_session is valid.")
        if res.status_code == 403:
            if res.text == "Forbidden":
                print(datetime.now().strftime("%H:%M:%S ") + "Your iksm_session is expired.")
                if self.param.session_token != "":
                    print(datetime.now().strftime("%H:%M:%S ") + "Regenerate iksm_session.")
                    # Regenerate iksm_session with session_token
                    self.param.iksm_session = iksm.get_cookie(self.param.session_token, LANG, VERSION)
            else:
                print(datetime.now().strftime("%H:%M:%S ") + "Unknown error.")
                message = datetime.now().strftime("%H:%M:%S Unknown error.\n")
                self.writeLog(message)
                sys.exit(1)
        
        url = "https://app.splatoon2.nintendo.net/api/coop_results"
        # print(datetime.now().strftime("%H:%M:%S ") + "Getting latest job id from SplatNet2.")
        res = requests.get(url, cookies=dict(iksm_session=self.param.iksm_session)).json()
        self.param.splatnet2 = int(res["summary"]["card"]["job_num"])
        self.param.output()

    def setConfig(self):
        session_token = iksm.log_in(VERSION)
        iksm_session = iksm.get_cookie(session_token, LANG, VERSION)
        webbrowser.open(URL)
        print(datetime.now().strftime("%H:%M:%S ") + "Login and Paste API token.")
        while True: # Waiting Input session_token & api-token
            try:
                token = input("")
                if len(token) == 64: # Simple Validation of api-token length
                    try:
                        int(token, 16) # Convert to Hex
                        print(datetime.now().strftime("%H:%M:%S ") + "Valid token.")
                        api_token = token
                        break
                    except ValueError:
                        print(datetime.now().strftime("%H:%M:%S ") + "Paste API token again.")
                else:
                    print(datetime.now().strftime("%H:%M:%S ") + "Paste API token again.")
            except KeyboardInterrupt:
                print("\nBye!")
                sys.exit(1)
        self.param.setup(iksm_session, session_token, api_token)

    def getJobId(self):
        url = "https://app.splatoon2.nintendo.net/api/coop_results"
        # print(datetime.now().strftime("%H:%M:%S ") + "Getting latest job id from SplatNet2.")
        res = requests.get(url, cookies=dict(iksm_session=self.param.iksm_session)).json()
        return int(res["summary"]["card"]["job_num"])

    def upload(self, resid):
        resid = str(resid)
        path = "json/" + resid + ".json"
        file = json.load(open(path, "r"))
        result = {"results": [file]}
        url = "https://salmon-stats-api.yuki.games/api/results"
        headers = {"Content-type": "application/json",
                   "Authorization": "Bearer " + self.param.api_token}
        res = requests.post(url, data=json.dumps(result), headers=headers)

        if res.status_code == 401:  # 認証エラー
            message = datetime.now().strftime("%H:%M:%S API token is invalid.\n")
            self.writeLog(message)
            sys.exit()
        if res.status_code == 200:  # 認証成功
            # レスポンスの変換
            text = json.loads(res.text)[0]
            if text["created"] == False:
                print(datetime.now().strftime("%H:%M:%S ") + resid + " skip.")
            else:
                print(datetime.now().strftime("%H:%M:%S ") + resid + " upload!")
        if res.status_code == 500:
            print(datetime.now().strftime("%H:%M:%S ") + resid + " failure.")
            message = datetime.now().strftime("%H:%M:%S " + resid + " : unrecoginized schedule id.\n")
            self.writeLog(message)
            with open("unupload_list.txt", mode="a") as f:
                f.write(resid + ".json\n") 

    def writeLog(self, message):
        with open("error.log", mode="a") as f:
            f.write(message)
        f.close()

    def uploadAll(self):
        file = []
        dir = os.listdir("json")
        for p in dir:
            file.append(p[0:-5])
        file.sort(key=int)
        
        results = [] # Initialize
        headers = {"Content-type": "application/json", "Authorization": "Bearer " + self.param.api_token}
        
        url = "https://salmon-stats-api.yuki.games/api/results"
        for job_id in file:
            if self.param.salmonstats < int(job_id):
                path = "json/" + job_id + ".json"
                results += [json.load(open(path, "r"))]
                if len(results) % 10 == 0:
                    res = requests.post(url, data=json.dumps({"results": results}), headers=headers)
                    results = []
                    if res.status_code == 200:
                        res = json.loads(res.text)
                        for r in res:
                            if r["created"] == False:
                                print(datetime.now().strftime("%H:%M:%S ") + str(r["job_id"]) + " skip.")
                            else:
                                print(datetime.now().strftime("%H:%M:%S ") + str(r["job_id"]) + " upload!.")
                            self.param.salmonstats = r["job_id"]
                            self.param.output()
                    sleep(5)
        # Remind Upload
        res = requests.post(url, data=json.dumps({"results": results}), headers=headers)
        if res.status_code == 200:
            res = json.loads(res.text)
            for r in res:
                if r["created"] == False:
                    print(datetime.now().strftime("%H:%M:%S ") + str(r["job_id"]) + " skip.")
                else:
                    print(datetime.now().strftime("%H:%M:%S ") + str(r["job_id"]) + " upload!.")
                self.param.salmonstats = r["job_id"]
                self.param.output()

    def getResults(self):
        self.param.splatnet2 = self.getJobId() 
        count = self.param.splatnet2 - 49 if self.param.splatnet2 - 50 >  self.param.local else self.param.local + 1
        if self.param.local == self.param.splatnet2:
            return
        for job_id in range(count, self.param.splatnet2 + 1):
            url = "https://app.splatoon2.nintendo.net/api/coop_results/" + \
                str(job_id)
            res = requests.get(url, cookies=dict(
                iksm_session=self.param.iksm_session)).text
            path = os.path.dirname(os.path.abspath(
                sys.argv[0])) + "/json/" + str(job_id) + ".json"
            with open(path, mode="w") as f:
                f.write(res)
            print(datetime.now().strftime("%H:%M:%S ") + "Saved " + str(job_id) + " from SplatNet2.")
            
            # Upload Result to SalmonStats
            if job_id > self.param.salmonstats:
                self.param.local = job_id
                self.upload(job_id)
            self.param.output()

if __name__ == "__main__":
    user = SalmonRec()
    user.uploadAll()
    
    print(datetime.now().strftime("%H:%M:%S ") + "Waiting New Result.")

    while True:
        user.getResults()
        sleep(10)
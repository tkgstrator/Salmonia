# -*- coding: utf-8 -*-
import sys
import json
import os
import webbrowser
import re
import requests
from datetime import datetime
from time import sleep
from more_itertools import chunked
import iksm

VERSION = "1.10.0"
LANG = "en-US"
URL = "https://salmon-stats.yuki.games/"


# 時刻付きでログを表示する
def Log(str):
    print(f'{datetime.now().strftime("%H:%M:%S")} {str}')


def CLog(str):
    print(f'\r{datetime.now().strftime("%H:%M:%S")} {str}', end="")


# ファイルまでのパスを返す
def FilePath(file):
    return f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/{file}"


def JsonPath(file):
    return f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/json/{file}.json"


class Salmonia():
    # クラス変数を初期化
    # nsa_id = None
    iksm_session = None
    session_token = None
    api_token = None
    job_num = {"splatnet2": 0, "salmonstats": 0, "local": 0}
    api_errors = 0

    def __init__(self):
        Log(f"Salmonia version {VERSION}")
        Log("Thanks @Yukinkling and @barley_ural!")

        try:
            with open(FilePath("config.json"), mode="r") as f:  # 設定ファイルがある場合
                params = json.load(f)
                # Log(params)
                self.iksm_session = params["iksm_session"]
                self.session_token = params["session_token"]
                self.api_token = params["api-token"]
                self.job_num = params["job_num"]
                if "json" not in os.listdir():
                    Log("Make JSON Directory")
                    os.mkdir("json")
                return
        except FileNotFoundError:  # 設定ファイルがない場合
            Log("config.json is not found")
            self.login()
        except json.decoder.JSONDecodeError:  # 設定ファイルのフォーマットがおかしい場合
            Log("config.json is broken")
            self.login()
        except Exception as error:
            Log(f"Fatal Error {error}")

    # ログインと設定ファイル生成
    def login(self):
        Log("Log in, right click the \"Select this account\" button, copy the link address, and paste it below:")
        webbrowser.open(iksm.log_in())
        while True:
            try:
                url_scheme = input("")
                session_token_code = re.search("de=(.*)&", url_scheme).group(1)
                user_info = iksm.get_cookie(session_token_code)
                self.iksm_session = user_info["iksm_session"]
                self.session_token = user_info["session_token"]
                Log("\nSuccess")
                break
            except KeyboardInterrupt:
                Log("\rKeyboard Interrupt")
                sys.exit(1)
            except AttributeError:
                Log("\rInvalid URL")
            except KeyError:
                Log("\rInvalid URL")
            except ValueError as error:
                Log(f"\rError Description {error}")
                sys.exit(1)
        webbrowser.open(URL)
        Log("Login and Paste API token")
        while True:
            try:
                api_token = input("")
                if len(api_token) == 64:
                    try:
                        int(api_token, 16)
                        self.api_token = api_token
                        Log("Success")
                        break
                    except ValueError:
                        Log("Paste API token again")
                else:
                    Log("Paste API token again")
            except KeyboardInterrupt:
                Log("Bye")
                sys.exit(1)
            except Exception as error:
                Log(f"\rError Description {error}")
                sys.exit(1)
        self.output()  # 設定ファイル書き込み

    # 設定ファイル書き込み
    def output(self):
        with open("config.json", mode="w") as f:
            data = {
                "iksm_session": self.iksm_session,
                "session_token": self.session_token,
                "api-token": self.api_token,
                "job_num": self.job_num,
                "api_errors": self.api_errors
            }
            json.dump(data, f, indent=4)

    def getJobId(self):
        try:
            url = "https://app.splatoon2.nintendo.net/api/coop_results"
            # Log(self.iksm_session)
            response = requests.get(url, cookies=dict(iksm_session=self.iksm_session)).json()
            return int(response["summary"]["card"]["job_num"])
        except:
            raise ValueError("Invalid/Expired iksm_session")

    def getResultFromSplatNet2(self):
        present = self.getJobId()
        preview = max(self.job_num["splatnet2"], present - 49)

        if present == preview:
            return

        for job_num in range(preview + 1, present + 1):
            Log(f"Result {job_num} downloading")
            url = f"https://app.splatoon2.nintendo.net/api/coop_results/{job_num}"
            response = requests.get(url, cookies=dict(iksm_session=self.iksm_session)).text
            with open(JsonPath(job_num), mode="w") as f:
                f.write(response)
        self.job_num["splatnet2"] = present
        self.allResultToSalmonStats(range(preview + 1, present + 1))

    # 起動時にJSONフォルダ内の未アップロードのリザルトを全てアップロード
    def allResultToSalmonStats(self, local=None):
        url = "https://salmon-stats-api.yuki.games/api/results"
        header = {"Content-type": "application/json", "Authorization": "Bearer " + self.api_token}

        # Salmon Statsの最新アップロード以上のIDのリザルトを取得
        if local == None:
            results = list(chunked(filter(lambda f: int(f) > self.job_num["salmonstats"], list(map(lambda f: f[0:-5], os.listdir("json")))), 10))
        else:
            results = list(chunked(local, 10))

        for result in results:
            data = list(map(lambda f: json.load(open(JsonPath(f), mode="r")), result))
            response = requests.post(url, data=json.dumps({"results": data}), headers=header)

            # ログを表示
            for response in json.loads(response.text):
                Log(f"{response['job_id']} -> {response['salmon_id']} uploading")
            # アップロードした最後のIDを更新
            self.job_num["salmonstats"] = int(max(result))
            sleep(5)


if __name__ == "__main__":
    try:
        user = Salmonia()
        user.allResultToSalmonStats()
        while True:
            CLog("Waiting New Results")
            user.getResultFromSplatNet2()
            user.output()  # 設定ファイルを更新
            sleep(5)
    except KeyboardInterrupt:
        Log("\nBye")
    except Exception as error:
        Log(error)

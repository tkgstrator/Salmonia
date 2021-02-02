# -*- coding: utf-8 -*-
import sys
import json
import os
import webbrowser
import re
from datetime import datetime
from time import sleep
import iksm

VERSION = "1.10.0"
LANG = "en-US"
URL = "https://salmon-stats.yuki.games/"


# 時刻付きでログを表示する
def Log(str):
    print(datetime.now().strftime("%H:%M:%S"), str)


# ファイルまでのパスを返す
def FilePath(path):
    return f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/{path}"


class Salmonia():
    # クラス変数を初期化
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
                Log(params)

                iksm_session = params["iksm_session"]
                session_token = params["session_token"]
                api_token = params["api-token"]

        except FileNotFoundError:  # 設定ファイルがない場合
            Log("config.json is not found")
        except json.decoder.JSONDecodeError:  # 設定ファイルのフォーマットがおかしい場合
            Log("config.json is broken")
        except Exception as error:
            Log(f"Fatal Error {error}")

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


if __name__ == "__main__":
    user = Salmonia()

    print("Log in, right click the \"Select this account\" button, copy the link address, and paste it below:")
    webbrowser.open(iksm.log_in())
    while True:
        try:
            url_scheme = input("")
            session_token_code = re.search("de=(.*)&", url_scheme).group(1)
            user_info = iksm.get_cookie(session_token_code)
            user.iksm_session = user_info["iksm_session"]
            user.session_token = user_info["session_token"]
            Log("\nSuccess")
            break
        except KeyboardInterrupt:
            print("\rKeyboard Interrupt")
            sys.exit(1)
        except AttributeError:
            print("\rInvalid URL")
        except KeyError:
            print("\rInvalid URL")
        except ValueError as error:
            print(f"\rError Description {error}")
            sys.exit(1)
    webbrowser.open(URL)
    Log("Login and Paste API token")
    while True:
        try:
            api_token = input("")
            if len(api_token) == 64:
                try:
                    int(api_token, 16)
                    user.api_token = api_token
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
            print(f"\rError Description {error}")
            sys.exit(1)
    user.output()  # 設定ファイル書き込み

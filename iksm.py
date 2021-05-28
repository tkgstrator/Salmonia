# eli fessler dedicated tkgling
# clovervidia
from builtins import input
import requests
import urllib
import json
import time
from datetime import datetime

session = requests.Session()
version = "1.11.0"


def log_in():
    url = "https://accounts.nintendo.com/connect/1.0.0/authorize"
    session_token_code_challenge = "tYLPO5PxpK-DTcAHJXugD7ztvAZQlo0DQQp3au5ztuM"
    parameters = {
        "state":                                "V6DSwHXbqC4rspCn_ArvfkpG1WFSvtNYrhugtfqOHsF6SYyX",
        "redirect_uri":                         "npf71b963c1b7b6d119://auth",
        "client_id":                            "71b963c1b7b6d119",
        "scope":                                "openid user user.birthday user.mii user.screenName",
        "response_type":                        "session_token_code",
        "session_token_code_challenge":         session_token_code_challenge,
        "session_token_code_challenge_method":  "S256",
        "theme":                                "login_form"
    }
    header = {
        "User-Agent":   f"Salmonia/{version} @tkgling"
    }

    response = session.get(url, headers=header, params=parameters)
    post_login = response.history[0].url
    return post_login


def get_session_token(session_token_code):
    try:
        print(f'{datetime.now().strftime("%H:%M:%S")} Getting Session Token')
        url = "https://accounts.nintendo.com/connect/1.0.0/api/session_token"
        session_token_code_verifier = "OwaTAOolhambwvY3RXSD-efxqdBEVNnQkc0bBJ7zaak"
        parameters = {
            "client_id":                    "71b963c1b7b6d119",
            "session_token_code":           session_token_code,
            "session_token_code_verifier":  session_token_code_verifier,
        }
        header = {
            "User-Agent":      f"Salmonia/{version} @tkgling",
            "Accept":          "application/json",
            "Content-Type":    "application/x-www-form-urlencoded",
            "Content-Length":  str(len(urllib.parse.urlencode(parameters))),
            "Host":            "accounts.nintendo.com",
        }

        response = session.post(url, headers=header, data=parameters)
        return json.loads(response.text)["session_token"]
    except:
        raise ValueError(json.loads(response.text)["error_description"])


def _get_access_token(session_token):
    try:
        url = "https://accounts.nintendo.com/connect/1.0.0/api/token"
        parameters = {
            "client_id":        "71b963c1b7b6d119",
            "grant_type":       "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token",
            "session_token":    session_token
        }
        header = {
            "Host":            "accounts.nintendo.com",
            "User-Agent":      f"Salmonia/{version} @tkgling",
            "Accept":          "application/json",
            "Content-Length":  str(len(urllib.parse.urlencode(parameters))),
        }

        response = requests.post(url, headers=header, json=parameters)
        return json.loads(response.text)["access_token"]
    except:
        raise ValueError("The provided session_token is invalid")


def _get_splatoon_token(access_token):
    try:
        url = "https://api-lp1.znc.srv.nintendo.net/v1/Account/Login"
        result = _call_flapg_api(access_token)
        parameter = {
            "parameter": {
                "f":            result["f"],
                "naIdToken":    result["p1"],
                "timestamp":    result["p2"],
                "requestId":    result["p3"],
                "naCountry":    "JP",
                "naBirthday":   "1990-01-01",
                "language":     "ja-JP"
            }
        }
        header = {
            "Host": "api-lp1.znc.srv.nintendo.net",
            "User-Agent":       f"Salmonia/{version} @tkgling",
            "Authorization":    "Bearer",
            "X-ProductVersion": f"{version}",
            "X-Platform":       "Android",
        }

        response = requests.post(url, headers=header, json=parameter)
        # print("SPLATOON TOKEN", response.text)
        return json.loads(response.text)["result"]["webApiServerCredential"]["accessToken"]
    except:
        raise ValueError(f"X-Product Version {version} is no longer available")


def _call_s2s_api(access_token, timestamp):
    try:
        url = "https://elifessler.com/s2s/api/gen2"
        parameters = {
            "naIdToken":    access_token,
            "timestamp":    timestamp
        }
        header = {
            "User-Agent":   f"Salmonia/{version} @tkgling",
        }

        response = requests.post(url, headers=header, data=parameters)
        if response.status_code != 200:
            raise ValueError("Too many requets")
        return json.loads(response.text)["hash"]
    except:
        raise ValueError("Too many requets")


def _call_flapg_api(access_token, type=True):
    try:
        url = "https://flapg.com/ika2/api/login?public"
        timestamp = int(time.time())

        header = {
            "x-token":  access_token,
            "x-time": str(timestamp),
            "x-guid": "037239ef-1914-43dc-815d-178aae7d8934",
            "x-hash": _call_s2s_api(access_token, timestamp),
            "x-ver": "3",
            "x-iid": "nso" if type == True else "app"
        }

        response = requests.get(url, headers=header)
        # print("F", response.text)
        return json.loads(response.text)["result"]
    except:
        raise ValueError("Upgrade required")


def _get_splatoon_access_token(splatoon_token):
    try:
        url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
        result = _call_flapg_api(splatoon_token, False)
        parameter = {
            "parameter": {
                "id":                   5741031244955648,
                "f":                    result["f"],
                "registrationToken":    result["p1"],
                "timestamp":            result["p2"],
                "requestId":            result["p3"],
            }
        }
        header = {
            "Host":             "api-lp1.znc.srv.nintendo.net",
            "User-Agent":       f"Salmonia/{version} @tkgling",
            "Authorization":    f"Bearer {splatoon_token}",
            "X-ProductVersion": f"{version}",
            "X-Platform":       "Android",
        }

        response = requests.post(url, headers=header, json=parameter)
        return json.loads(response.text)["result"]["accessToken"]
    except:
        raise ValueError(f"X-Product Version {version} is no longer available")


def _get_iksm_session(splatoon_access_token):
    url = "https://app.splatoon2.nintendo.net"
    header = {
        "Cookie": "iksm_session=",
        "X-GameWebToken":   splatoon_access_token
    }

    response = requests.get(url, headers=header)
    return response.cookies["iksm_session"]


def get_cookie(session_token):
    print(f'{datetime.now().strftime("%H:%M:%S")} Getting Access Token')
    access_token = _get_access_token(session_token)
    print(f'{datetime.now().strftime("%H:%M:%S")} Getting Splatoon Token')
    splatoon_token = _get_splatoon_token(access_token)
    print(f'{datetime.now().strftime("%H:%M:%S")} Getting Splatoon Access Token')
    splatoon_access_token = _get_splatoon_access_token(splatoon_token)
    print(f'{datetime.now().strftime("%H:%M:%S")} Getting Iksm Session')
    iksm_session = _get_iksm_session(splatoon_access_token)

    return iksm_session

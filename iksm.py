from dataclasses import asdict, dataclass
from xml.dom import NotFoundErr
from dataclasses_json import dataclass_json
from typing import List, Type
from typing import Optional
from requests import Session
import requests
import re
import urllib
import json
import sys
import time
import os
from enum import Enum


@dataclass_json
@dataclass
class ErrorNSO:
    error: str
    error_description: str


@dataclass_json
@dataclass
class ErrorHash:
    error: str


@dataclass_json
@dataclass
class Information:
    minimumOsVersion: str
    version: str
    currentVersionReleaseDate: str


@dataclass_json
@dataclass
class AppVersion:
    resultCount: int
    results: List[Information]


@dataclass_json
@dataclass
class ErrorAPP:
    status: str
    correlationId: str
    errorMessage: str


@dataclass_json
@dataclass
class SessionToken:
    code: str
    session_token: str


@dataclass_json
@dataclass
class AccessToken:
    access_token: str
    scope: List[str]
    token_type: str
    id_token: str
    expires_in: int


@dataclass_json
@dataclass
class Credential:
    accessToken: str
    expiresIn: int


@dataclass_json
@dataclass
class FriendCode:
    regenerable: bool
    regenerableAt: int
    id: str


@dataclass_json
@dataclass
class Membership:
    active: bool


@dataclass_json
@dataclass
class NintendoAccount:
    membership: Membership


@dataclass_json
@dataclass
class Links:
    nintendoAccount: NintendoAccount
    friendCode: FriendCode


@dataclass_json
@dataclass
class Permissions:
    presence: str


@dataclass_json
@dataclass
class Game:
    pass


@dataclass_json
@dataclass
class Presence:
    state: str
    updatedAt: int
    logoutAt: int
    game: Game


@dataclass_json
@dataclass
class User:
    id: int
    nsaId: str
    imageUri: str
    name: str
    supportId: str
    isChildRestricted: bool
    etag: str
    links: Links
    permissions: Permissions
    presence: Presence


@dataclass_json
@dataclass
class SplatoonTokenResult:
    user: User
    webApiServerCredential: Credential
    firebaseCredential: Credential


@dataclass_json
@dataclass
class SplatoonToken:
    status: int
    result: SplatoonTokenResult
    correlationId: str


@dataclass_json
@dataclass
class SplatoonAccessTokenResult:
    accessToken: str
    expiresIn: int


@dataclass_json
@dataclass
class SplatoonAccessToken:
    status: int
    result: SplatoonAccessTokenResult
    correlationId: str


@dataclass_json
@dataclass
class Hash:
    hash: str


@dataclass_json
@dataclass
class FlapgResult:
    f: str
    p1: str
    p2: str
    p3: str


@dataclass_json
@dataclass
class Flapg:
    result: FlapgResult


@dataclass_json
@dataclass
class JobNum:
    local: int = 0
    splatnet2: int = 0


@dataclass_json
@dataclass
class UserInfo:
    session_token: str
    iksm_session: str
    nsa_id: str
    friend_code: str
    result_id: int = 0
    host_type: int = 0
    name: str = "(undefined name)"
    noupload: bool = False
    multi: bool = False

    @property
    def job_num(self):
        pass

    @job_num.getter
    def job_num(self):
        return self.result_id

    @job_num.setter
    def job_num(self, job_num: int):
        self.result_id = max(self.result_id, job_num)
        save(self)


session_token_code_challenge = "tYLPO5PxpK-DTcAHJXugD7ztvAZQlo0DQQp3au5ztuM"
session_token_code_verifier = "OwaTAOolhambwvY3RXSD-efxqdBEVNnQkc0bBJ7zaak"


class Type(Enum):
    NSO = "nso"
    APP = "app"


def get_cookie(session: Session, url_scheme: str, version: str, host_type: int = 0) -> UserInfo:
    RAWOut = open(1, 'w', encoding='utf8', closefd=False)
    session_token = get_session_token(session, url_scheme, version)
    print(f"Session token: {session_token}", file=RAWOut)
    access_token = get_access_token(session, session_token.session_token, version)
    print(f"Access token: {access_token}", file=RAWOut)
    splatoon_token = get_splatoon_token(session, access_token, version)
    print(f"Splatoon token: {splatoon_token}", file=RAWOut)
    splatoon_access_token = get_splatoon_access_token(session, splatoon_token, version)
    print(f"Splatoon Access Token: {splatoon_access_token}", file=RAWOut)
    iksm_session = get_iksm_session(session, splatoon_access_token, version)
    print(f"Iksm session: {iksm_session}", file=RAWOut)
    return save(
        UserInfo(
            session_token.session_token,
            iksm_session,
            splatoon_token.result.user.nsaId,
            splatoon_token.result.user.links.friendCode.id,
            # should result_id for an initial run be 0?
            result_id=__get_latest_result_id(),
            host_type=host_type,
            name=splatoon_token.result.user.name,
        )
    )


def __get_latest_result_id() -> int:
    try:
        if len(os.listdir("results")) == 0:
            return 0
        return max(
            list(
                map(
                    lambda x: int(os.path.splitext(os.path.basename(x))[0]),
                    os.listdir("results"),
                )
            )
        )
    except FileNotFoundError:
        return 0


def renew_cookie(session: Session, userinfo: UserInfo, version: str, host_type: int = 0) -> UserInfo:
    RAWOut = open(1, 'w', encoding='utf8', closefd=False)
    access_token = get_access_token(session, userinfo.session_token, version)
    print(f"Access token: {access_token}", file=RAWOut)
    splatoon_token = get_splatoon_token(session, access_token, version)
    print(f"Splatoon token: {splatoon_token}", file=RAWOut)
    splatoon_access_token = get_splatoon_access_token(session, splatoon_token, version)
    print(f"Splatoon Access Token: {splatoon_access_token}", file=RAWOut)
    iksm_session = get_iksm_session(session, splatoon_access_token, version)
    print(f"Iksm session: {iksm_session}", file=RAWOut)
    return save(
        UserInfo(
            userinfo.session_token,
            iksm_session,
            splatoon_token.result.user.nsaId,
            splatoon_token.result.user.links.friendCode.id,
            result_id=userinfo.result_id,
            host_type=host_type,
            name=splatoon_token.result.user.name,
            multi=userinfo.multi,
            nouload=userinfo.noupload,
        )
    )


def get_session_token_code(session: Session, version: str):
    url = "https://accounts.nintendo.com/connect/1.0.0/authorize"

    parameters = {
        "state": "V6DSwHXbqC4rspCn_ArvfkpG1WFSvtNYrhugtfqOHsF6SYyX",
        "redirect_uri": "npf71b963c1b7b6d119://auth",
        "client_id": "71b963c1b7b6d119",
        "scope": "openid user user.birthday user.mii user.screenName",
        "response_type": "session_token_code",
        "session_token_code_challenge": session_token_code_challenge,
        "session_token_code_challenge_method": "S256",
        "theme": "login_form",
    }
    headers = {
        "user-agent": f"Salmonia/{version} @tkgling",
    }
    response = session.get(url, headers=headers, params=parameters)
    return response.history[0].url


def get_session_token(session: Session, url_scheme: str, version: str) -> SessionToken:
    session_token_code = re.search("de=(.*)&", url_scheme).group(1)

    url = "https://accounts.nintendo.com/connect/1.0.0/api/session_token"
    parameters = {
        "client_id": "71b963c1b7b6d119",
        "session_token_code": session_token_code,
        "session_token_code_verifier": session_token_code_verifier,
    }
    headers = {
        "user-agent": f"Salmonia/{version} @tkgling",
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "content-length": str(len(urllib.parse.urlencode(parameters))),
        "host": "accounts.nintendo.com",
    }

    try:
        response = session.post(url, headers=headers, data=parameters).text
        return SessionToken.from_json(response)
    except:
        response = ErrorNSO.from_json(response)
        print(f"TypeError: {response.error_description}")
        sys.exit(1)


def get_access_token(session: Session, session_token: str, version: str) -> AccessToken:
    url = "https://accounts.nintendo.com/connect/1.0.0/api/token"
    parameters = {
        "client_id": "71b963c1b7b6d119",
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer-session-token",
        "session_token": session_token,
    }
    headers = {
        "Host": "accounts.nintendo.com",
        "User-Agent": f"Salmonia/{version} @tkgling",
        "Accept": "application/json",
        "Content-Length": str(len(urllib.parse.urlencode(parameters))),
    }
    try:
        response = session.post(url, headers=headers, json=parameters).text
        return AccessToken.from_json(response)
    except:
        response = ErrorNSO.from_json(response)
        print(f"TypeError: {response.error_description}")
        sys.exit(1)


def get_hash(session: Session, access_token: str, timestamp: int, version: str) -> Hash:
    url = "https://s2s-hash-server.herokuapp.com/hash"
    parameters = {"naIdToken": access_token, "timestamp": timestamp}
    header = {
        "User-Agent": f"Salmonia/{version} @tkgling",
    }
    try:
        response = session.post(url, headers=header, data=parameters)
        return Hash.from_json(response.text)
    except:
        response = ErrorHash.from_json(response.text)
        print(f"TypeError: {response.error}, response")
        sys.exit(1)


def get_flapg(session: Session, access_token: str, version: str, type: Type) -> Flapg:
    url = "https://flapg.com/ika2/api/login"
    timestamp = int(time.time())
    headers = {
        "x-token": access_token,
        "x-time": str(timestamp),
        "x-guid": "037239ef-1914-43dc-815d-178aae7d8934",
        "x-hash": get_hash(session, access_token, timestamp, version).hash,
        "x-ver": "3",
        "x-iid": type.value,
    }
    try:
        response = session.get(url, headers=headers)
        return Flapg.from_json(response.text)
    except:
        response = ErrorHash.from_json(response)
        print(f"TypeError: {response.error}")
        sys.exit(1)


def get_splatoon_token(session: Session, access_token: AccessToken, version: str):
    url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"
    result = get_flapg(session, access_token.access_token, version, Type.NSO).result
    parameters = {
        "parameter": {
            "f": result.f,
            "naIdToken": result.p1,
            "timestamp": result.p2,
            "requestId": result.p3,
            "naCountry": "JP",
            "naBirthday": "1990-01-01",
            "language": "ja-JP",
        }
    }
    headers = {
        "Host": "api-lp1.znc.srv.nintendo.net",
        "User-Agent": f"Salmonia/{version} @tkgling",
        "Authorization": "Bearer",
        "X-ProductVersion": f"{version}",
        "X-Platform": "Android",
    }
    try:
        response = session.post(url, headers=headers, json=parameters)
        return SplatoonToken.from_json(response.text)
    except:
        response = ErrorNSO.from_json(response)
        print(f"TypeError: {response.error}")


def get_splatoon_access_token(session: Session, splatoon_token: SplatoonToken, version: str):
    url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
    access_token = splatoon_token.result.webApiServerCredential.accessToken
    result = get_flapg(session, access_token, version, Type.APP).result
    parameters = {
        "parameter": {
            "id": 5741031244955648,
            "f": result.f,
            "registrationToken": result.p1,
            "timestamp": result.p2,
            "requestId": result.p3,
        }
    }
    headers = {
        "Host": "api-lp1.znc.srv.nintendo.net",
        "User-Agent": f"Salmonia/{version} @tkgling",
        "Authorization": f"Bearer {access_token}",
        "X-ProductVersion": f"{version}",
        "X-Platform": "Android",
    }

    try:
        response = session.post(url, headers=headers, json=parameters)
        return SplatoonAccessToken.from_json(response.text)
    except:
        response = ErrorAPP.from_json(response)
        print(f"TypeError: {response.errorMessage}")


def get_iksm_session(session: Session, splatoon_access_token: SplatoonAccessToken, version: str):
    url = "https://app.splatoon2.nintendo.net"
    headers = {
        "Cookie": "iksm_session=",
        "X-GameWebToken": splatoon_access_token.result.accessToken,
    }

    try:
        response = session.get(url, headers=headers)
        return response.cookies["iksm_session"]
    except:
        print(f"TypeError: invalid splatoon access token")


def get_app_version(session: Session) -> str:
    url = "https://itunes.apple.com/lookup?id=1234806557"
    try:
        response = session.get(url)
        return AppVersion.from_json(response.text).results[0].version
    except:
        print(f"TypeError: invalid id")


def request(session: Session, url: str, iksm_session: str) -> str:
    cookies = dict(iksm_session=iksm_session)
    return session.get(url, cookies=cookies).text


def post(session: Session, url: str, json: json):
    session.post(url, json=json)


def save(data: UserInfo) -> UserInfo:
    try:
        fname = (data.nsa_id + ".json") if data.multi else "config.json"
        with open(fname, "w") as f:
            json.dump(asdict(data), f, indent=4)
        return data
    except:
        raise TypeError


def load(player_id = None) -> UserInfo:
    prefix = "config" if player_id is None else player_id
    try:
        with open(prefix + ".json", "r") as f:
            ui = UserInfo.from_json(f.read())
            if not player_id is None:
                ui.multi = True
            return ui
    except Exception as e:
        raise FileNotFoundError

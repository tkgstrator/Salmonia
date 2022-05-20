from dataclasses import asdict, dataclass
from datetime import datetime
from typing_extensions import Self
from dataclasses_json import dataclass_json
from typing import List, Type
from dotenv import load_dotenv
import requests
import json
import iksm
import sys
import os
import time
from enum import Enum

# Load Environment Variables
load_dotenv()


class Status(Enum):
    CREATED = "created"
    UPDATED = "updated"


class APIVersion(Enum):
    V1 = "v1"
    V2 = "v2"


class Environment(Enum):
    Production = 0
    Development = 1
    Sandbox = 2
    Local = 3

    def __init__(self, value: int):
        self.id = id

    def mode(self) -> str:
        if self == Environment.Production:
            return "Production"
        elif self == Environment.Development:
            return "Development"
        elif self == Environment.Sandbox:
            return "Sandbox"
        elif self == Environment.Local:
            return "Local"

    def url(self) -> str:
        if self == Environment.Production:
            return "http://api.splatnet2.com"
        elif self == Environment.Development:
            return "http://api-dev.splatnet2.com"
        elif self == Environment.Sandbox:
            return "http://api-sandbox.splatnet2.com"
        elif self == Environment.Local:
            return "http://localhost:3000"


@dataclass_json
@dataclass
class UploadResult:
    salmon_id: int
    status: Status


@dataclass_json
@dataclass
class UploadResults:
    results: List[UploadResult]


@dataclass_json
@dataclass
class Card:
    job_num: int
    help_total: int
    kuma_point_total: int
    golden_ikura_total: int
    kuma_point: int
    ikura_total: int


@dataclass_json
@dataclass
class Stat:
    team_ikura_total: int
    help_total: int
    grade_point: int
    dead_total: int
    my_ikura_total: int
    # schedule: Schedule
    kuma_point_total: int
    clear_num: int
    team_golden_ikura_total: int
    failure_counts: List[int]
    end_time: int
    job_num: int
    my_golden_ikura_total: int
    start_time: int
    # grade: StatGrade


@dataclass_json
@dataclass
class Summary:
    stats: List[Stat]
    card: Card


@dataclass_json
@dataclass
class Results:
    summary: Summary


def __get_launch_mode() -> int:
    try:
        return int(os.getenv("LAUNCH_MODE"))
    except:
        return 0


session = requests.Session()
environment = Environment(__get_launch_mode())


class Salmonia:
    version = iksm.get_app_version()

    def __init__(self):
        if not os.path.exists("results"):
            os.mkdir("results")
        print(f"Salmonia v{self.version} for Splatoon 2 ({environment.mode()})")
        try:
            self.userinfo: iksm.UserInfo = iksm.load()
            self.upload_all_result()
        except FileNotFoundError as error:
            self.sign_in()
            self.userinfo: iksm.UserInfo = iksm.load()
            self.upload_all_result()

    def sign_in(self):
        print(iksm.get_session_token_code(self.version))
        while True:
            try:
                iksm.get_cookie(input(""), self.version)
                break
            except KeyboardInterrupt:
                sys.exit(0)

    def __request_with_auth(self, url):
        response = session.get(
            url, cookies={"iksm_session": self.userinfo.iksm_session}
        )
        return response

    def get_latest_result_id(self) -> int:
        try:
            url = "https://app.splatoon2.nintendo.net/api/coop_results"
            response = Results.from_json(self.__request_with_auth(url).text)
            return response.summary.card.job_num
        except KeyError:
            self.userinfo = iksm.renew_cookie(self.userinfo.session_token, self.version)
            url = "https://app.splatoon2.nintendo.net/api/coop_results"
            response = Results.from_json(self.__request_with_auth(url).text)
            return response.summary.card.job_num

    def get_local_latest_result_id(self) -> int:
        if not os.path.exists("results"):
            os.mkdir("results")
        results = os.listdir("results")
        if len(results) == 0:
            return 0
        else:
            return max(
                list(
                    map(
                        lambda x: int(os.path.splitext(os.path.basename(x))[0]), results
                    )
                )
            )

    def __get_result(self, result_id) -> json:
        url = f"https://app.splatoon2.nintendo.net/api/coop_results/{result_id}"
        response = self.__request_with_auth(url).json()
        with open(f"results/{result_id}.json", "w") as f:
            json.dump(response, f)
        return response

    def upload_result(self, result_id: int):
        result = self.__get_result(result_id)
        url = f"{environment.url()}/results"
        parameters = {"results": [result]}
        try:
            res = session.post(url, json=parameters)
            response = UploadResults.from_json(res.text)
            for result in response.results:
                print(
                    f"\r{datetime.now().strftime('%H:%m:%S')} Uploaded {result_id}",
                    end="",
                )
                self.userinfo.job_num = max(result_id, self.userinfo.job_num)
        except Exception as error:
            print(f"\rError {res.status_code}")
            sys.exit(1)

    def upload_all_result(self):
        latest_result_id = self.get_latest_result_id()
        local_result_id = self.get_local_latest_result_id()
        if environment == Environment.Local:
            local_result_id -= 5
        if latest_result_id == local_result_id:
            print(f"\r{datetime.now().strftime('%H:%m:%S')} No new results", end="")
        oldest_result_id = max(local_result_id + 1, latest_result_id - 49)
        for result_id in range(oldest_result_id, latest_result_id + 1):
            self.upload_result(result_id)
            time.sleep(1)

from dataclasses import asdict, dataclass
from datetime import datetime
from typing_extensions import Self
from dataclasses_json import dataclass_json
from typing import List, Type
from dotenv import load_dotenv
from requests import Session
import requests
import json
import iksm
import sys
import os
import time
from enum import Enum


class Status(Enum):
    CREATED = "created"
    UPDATED = "updated"


class APIVersion(Enum):
    V1 = "v1"
    V2 = "v2"


class ResultType(Enum):
    LOCAL = 0
    ONLINE = 1


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
            return "https://api.splatnet2.com/v1"
        elif self == Environment.Development:
            return "https://api-dev.splatnet2.com/v1"
        elif self == Environment.Sandbox:
            return "https://api-sandbox.splatnet2.com/v1"
        elif self == Environment.Local:
            return "http://localhost:3000/v1"


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


class Salmonia:

    def __init__(self, player_id = None):
        if not os.path.exists("results"):
            os.mkdir("results")
        self.session = Session()
        self.version = iksm.get_app_version(self.session)
        print(f"Salmonia v{self.version} for Splatoon 2")
        try:
            self.userinfo: iksm.UserInfo = iksm.load(player_id)
            self.host_type = Environment(self.userinfo.host_type)
            self.uploaded_result_id = self.userinfo.result_id
            print(f"Launch Mode ({self.host_type.mode()})")
        except FileNotFoundError:
            self.sign_in()
            sys.exit(0)
        self.rotation = { 'start' : 0, 'end': 0}
        self.initializing = True
        self.upload_error = False

    def sign_in(self):
        print(iksm.get_session_token_code(self.session, self.version))
        while True:
            try:
                # Get cookie for Production Mode
                iksm.get_cookie(self.session, input(""), self.version)
                break
            except KeyboardInterrupt:
                sys.exit(0)

    def __request_with_auth(self, url):
        response = self.session.get(
            url, cookies={"iksm_session": self.userinfo.iksm_session}
        )
        return response

    def __renew_cookie(self):
        self.version = iksm.get_app_version(self.session)
        newuserinfo: iksm.UserInfo = iksm.renew_cookie(self.session, self.userinfo, 
                                                        self.version, self.host_type.value)
        self.userinfo = newuserinfo
        self.session = Session()

    def get_latest_result_id(self) -> int:
        try:
            url = "https://app.splatoon2.nintendo.net/api/coop_results"
            response = Results.from_json(self.__request_with_auth(url).text)
            return response.summary.card.job_num
        except KeyError:
            self.__renew_cookie()
            # retry should be a loop or exit gracefully with a warning
            url = "https://app.splatoon2.nintendo.net/api/coop_results"
            response = Results.from_json(self.__request_with_auth(url).text)
            return response.summary.card.job_num
        except Exception as e:
            print(f"Uncaught exception : {e}")
            sys.exit(1)

    def get_local_latest_result_id(self) -> int:
        fullpath = "results"
        if not os.path.exists(fullpath):
            os.mkdir(fullpath)
        if self.userinfo.multi:
            fullpath = f"results/{self.userinfo.nsa_id}"
            if not os.path.exists(fullpath):
                os.mkdir(fullpath)
        results = os.listdir(fullpath)
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

    def get_local_result_ids(self) -> List[int]:
        # If there is no local results, return empty list
        fullpath = "results"
        if not os.path.exists(fullpath):
            os.mkdir(fullpath)
        if self.userinfo.multi:
            fullpath = f"results/{self.userinfo.nsa_id}"
            if not os.path.exists(fullpath):
                os.mkdir(fullpath)
        results = os.listdir(fullpath)
        if len(results) == 0:
            return [0]
        else:
            return sorted(
                list(
                    map(
                        lambda x: int(os.path.splitext(os.path.basename(x))[0]), results
                    )
                )
            )

    def __get_rotation(self) -> dict:
        url = "https://app.splatoon2.nintendo.net/api/coop_schedules"
        response = self.__request_with_auth(url).json()
        try:
            first = response['schedules'][0]
        except KeyError:
            self.__renew_cookie()
            response = self.__request_with_auth(url).json()
            first = response['schedules'][0]
        return { 'start': first['start_time'], 'end': first['end_time']}
    
    def __get_result(self, result_id) -> json:
        url = f"https://app.splatoon2.nintendo.net/api/coop_results/{result_id}"
        response = self.__request_with_auth(url).json()
        path = f"results/{self.userinfo.nsa_id}/{result_id}.json" if self.userinfo.multi else f"results/{result_id}.json"
        with open(path, "w") as f:
            json.dump(response, f)
        return response

    def __get_local_result(self, result_id) -> json:
        path = f"results/{self.userinfo.nsa_id}/{result_id}.json" if self.userinfo.multi else f"results/{result_id}.json"
        with open(path, mode="r") as f:
            return json.load(f)

    def __upload_result(self, result_id: int, type: ResultType):
        # Load a result
        if type == ResultType.ONLINE:
            result = self.__get_result(result_id)
        if type == ResultType.LOCAL:
            result = self.__get_local_result(result_id)

        # If we got an upload error, don't upload what was downloaded
        # if will be attempted next run
        if self.upload_error:
            return

        # Upload a result
        url = f"{self.host_type.url()}/results"
        parameters = {"results": [result]}
        try:
            res = self.session.post(url, json=parameters)
            response = UploadResults.from_json(res.text)
            for result in response.results:
                print(
                    f"\r{datetime.now().strftime('%m-%d %H:%M:%S')} Uploaded {self.userinfo.nsa_id}/{result_id} -> {result.salmon_id}",
                    end="",
                )
                self.userinfo.job_num = max(result_id, self.userinfo.job_num)
                time.sleep(1)
        except Exception as error:
            self.upload_error = True

    def upload_local_result(self):
        unuploaded_result_ids = list(
            filter(lambda x: x > self.uploaded_result_id, self.get_local_result_ids())
        )

        print(f"Unuploaded Results ({len(unuploaded_result_ids)})")
        # Upload local results
        for result_id in unuploaded_result_ids:
            self.__upload_result(result_id, ResultType.LOCAL)

    def upload_all_result(self):
        # First run or after an error, upload local results
        if self.upload_error or self.initializing:
            self.upload_error = False
            self.upload_local_result()

        curtime = time.time()
        # Check if Salmon Run is open (we allow 10mn for an extra run)
        if (self.rotation['end'] == 0) or (curtime > (self.rotation['end'] + 600)):
            self.rotation = self.__get_rotation()
        if self.initializing:
            self.initializing = False
        elif curtime < self.rotation['start']:
            print(f"\r{datetime.now().strftime('%m-%d %H:%M:%S')} {self.userinfo.nsa_id} Salmon Run closed", end="")
            return


        # Get latest result id from SplatNet2
        latest_result_id = self.get_latest_result_id()
        # Get latest result id from results directory
        local_result_id = self.get_local_latest_result_id()

        if latest_result_id == local_result_id:
            print(f"\r{datetime.now().strftime('%m-%d %H:%M:%S')} {self.userinfo.nsa_id} No new results", end="")
            return
        # SplatNet2 does not have results which job id less than the latest_result_id - 49
        oldest_result_id = max(local_result_id + 1, latest_result_id - 49)

        for result_id in range(oldest_result_id, latest_result_id + 1):
            self.__upload_result(result_id, ResultType.ONLINE)

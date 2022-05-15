from dataclasses import asdict, dataclass
from typing_extensions import Self
from dataclasses_json import dataclass_json
from typing import List, Type
import requests
import json
import iksm
import sys
import os
from enum import Enum


class Status(Enum):
    CREATED = "created"
    UPDATED = "updated"


class APIVersion(Enum):
    V1 = "v1"
    V2 = "v2"


class Environment(Enum):
    Development = "Development"
    Production = "Production"
    Sandbox = "Sandbox"
    Local = "Local"

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


session = requests.Session()
environment = Environment.Local


class Salmonia:
    userinfo = None
    version = iksm.get_app_version()

    def __init__(self):
        print(f"Salmonia v{self.version} for Splatoon 2 ({environment.value})")
        try:
            self.userinfo = iksm.load()
            print(self.userinfo)
            result_id = self.get_latest_result_id()
            self.upload_result(result_id)
        except FileNotFoundError:
            self.sign_in()
            sys.exit(0)

    def sign_in(self):
        print(iksm.get_session_token_code(self.version))
        while True:
            try:
                iksm.get_cookie(input(""), self.version)
            except KeyboardInterrupt:
                sys.exit(0)

    def __request_with_auth(self, url):
        response = session.get(
            url, cookies={"iksm_session": self.userinfo.iksm_session}
        )
        return response

    def get_latest_result_id(self) -> int:
        url = "https://app.splatoon2.nintendo.net/api/coop_results"
        response = Results.from_json(self.__request_with_auth(url).text)
        return response.summary.card.job_num

    def __get_result(self, result_id) -> json:
        url = f"https://app.splatoon2.nintendo.net/api/coop_results/{result_id}"
        response = self.__request_with_auth(url).json()
        return response

    def upload_result(self, result_id):
        result = self.__get_result(result_id)
        url = f"{environment.url()}/results"
        parameters = {"results": [result]}
        response = UploadResults.from_json(session.post(url, json=parameters).text)
        for result in response.results:
            print(f"Uploaded {result.salmon_id} => {result.status.value}")

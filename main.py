import sys
import os
from salmonia import Salmonia
import iksm
import salmonia
import time
import schedule
import json
import argparse


def main(args):
    if args.multi:
        with open("multi.json", 'r', encoding="utf-8") as f:
            players = json.load(f)
            interval_offset = 0
            for player in players['list']:
                s = Salmonia(player)
                schedule.every(10+interval_offset).seconds.do(s.upload_all_result)
                interval_offset += 1
    else:
        session = Salmonia()
        schedule.every(10).seconds.do(session.upload_all_result)
    while True:
        schedule.run_pending()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-multi', action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()
    main(args)

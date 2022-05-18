import sys
import os
from salmonia import Salmonia
import iksm
import salmonia
import time
import schedule


def main():
    session = Salmonia()
    schedule.every(10).seconds.do(session.upload_all_result)
    while True:
        schedule.run_pending()


if __name__ == "__main__":
    main()

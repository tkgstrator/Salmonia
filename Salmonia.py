# -*- coding: utf-8 -*-
import sys
import json
import os
import webbrowser
import re
from datetime import datetime
from time import sleep
import iksm

if __name__ == "__main__":

    print("Log in, right click the \"Select this account\" button, copy the link address, and paste it below:")
    webbrowser.open(iksm.log_in())
    while True:
        try:
            url_scheme = input("")
            session_token_code = re.search("de=(.*)&", url_scheme).group(1)
            iksm.get_cookie(session_token_code)
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
    print("\rDone")

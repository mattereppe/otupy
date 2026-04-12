#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
import logging
import sys
import time
import otupy as oc2
from otupy.types.data.uri import URI
from otupy.types.targets.file import File
from otupy.profiles.rcli.data.process import Process
from otupy.profiles.rcli.targets.processes import Processes

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer

import otupy.profiles.rcli as rcli

# logging.basicConfig(filename='openc2.log',level=logging.DEBUG)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("openc2producer")


def main():
    logger.info("Creating Producer")
    p = oc2.Producer("producer2.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))
    pf = rcli.Specifiers({})
    arg = rcli.Args({"response_requested": oc2.ResponseType.complete})

    arg = rcli.Args(
        {
            "start_time": oc2.DateTime(time.time() * 1000 + 3000),
            # "stop_time" :  oc2.DateTime(time.time() * 1000 + 12000)
        }
    )

    execute = Process({"executable": File({"name": "script.sh"})})
    command = Process(name="code", command_line="_")
    command2 = Process({"name": "code", "command_line": "__"})
    procs = Processes()
    procs.append(command)
    procs.append(command2)

    cmd = oc2.Command(oc2.Actions.start, procs, arg, actuator=pf)

    logger.info("Sending " "command: %s", cmd)
    resp = p.sendcmd(cmd)
    logger.info("Got response: %s", resp)


if __name__ == "__main__":
    main()

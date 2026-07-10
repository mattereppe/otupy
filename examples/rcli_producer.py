#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
import logging
import hashlib
from argparse import ArgumentParser

import otupy as oc2
from otupy.types.data.uri import URI
from otupy.types.targets.file import File
from otupy.profiles.rcli import Files
from otupy.profiles.rcli.data.process import Process
from otupy.profiles.rcli.targets.processes import Processes

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer

import otupy.profiles.rcli as rcli

# logging.basicConfig(filename='openc2.log',level=logging.DEBUG)
"""logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('openc2producer')"""
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)
# Create stdout handler for logging to the console
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True))

hdls = [stdout_handler]
# Add both handlers to the logger
logger.addHandler(stdout_handler)
# Add file logger
file_handler = logging.FileHandler("controller_rcli_query_features.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(oc2.LogFormatter(datetime=True, name=True, datefmt="%t"))
logger.addHandler(file_handler)

def main():

    arguments = ArgumentParser()
    arguments.add_argument("--start", action="store_true", help="Start cli")
    arguments.add_argument("--stop", help="Stop process")
    arguments.add_argument("--copy", help="Copy file or url")
    arguments.add_argument("--delete", action="store_true", help="Delete file")
    arguments.add_argument("--query", action="store_true", help="Query features")
    arguments.add_argument("--cmd", default="", help="Run the given command [filebeat]")
    arguments.add_argument("--server", default="127.0.0.1", help="Select IP address of the Consumer [default=localhost]")
    arguments.add_argument("--port", default="8080", help="Select TCP port of the Consumer [default=8080]")
    args = arguments.parse_args()

    logger.info("Creating Producer")
    p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer(args.server, args.port))

    pf = rcli.Specifiers({"asset_id": "rcli-example"})
    arg = rcli.Args({"response_requested": oc2.ResponseType.complete})

    if args.query:
        cmd = oc2.Command(oc2.Actions.query, oc2.Features([oc2.Feature.clicommands]), arg, actuator=pf)
    elif args.start:
        execute = Process({"executable": File({"name": "script.sh"})})
#        command = Process(name="top", command_line="")
        command = Process(name="fprobe", command_line="-l 2 -i ens18 localhost:4555")
#        command2 = Process({"name": "code", "command_line": "pwd"})
        procs = Processes()
        procs.append(command)
#        procs.append(command2)
        cmd = oc2.Command(oc2.Actions.start, procs, arg, actuator=pf)

        # TODO: extract pid
    elif args.stop:
        processes = Processes()
        processes.append(Process(pid=args.stop))
        cmd = oc2.Command(oc2.Actions.stop, processes, arg, actuator=pf)
    elif args.copy:
        arg = rcli.Args(
            {
                "storage": File({"path": "/test", "name": "mymessage.bin"}),
            }
        )
    
#bcontent = b"My binary payssssload"
        with open(args.copy, 'rb') as f:
            bcontent = f.read()
        uri = "https://www.w3.org/TR/png/iso_8859-1.txt"
    
        h = oc2.Hashes({"md5": oc2.Binaryx(hashlib.md5(bcontent).digest())})
        a = oc2.Artifact(
            mime_type="application/json",
#            payload=oc2.Payload(URI(uri)),
             payload=oc2.Binary(bcontent),
             hashes= h
        )
        cmd = oc2.Command(oc2.Actions.copy, a, arg, actuator=pf)
    elif args.delete:
        files = Files()
        files.append(File({"path": "/test", "name": "mymessage.bin"}))
        cmd = oc2.Command(oc2.Actions.delete, files, arg, actuator=pf)





    logger.info("Sending command: %s", cmd)
    resp = p.sendcmd(cmd)
    logger.info("Got response: %s", resp)
    if args.start:
        pid = resp.content['results']['process_status'][0]['pid']
        print("Pid: ", pid)



if __name__ == "__main__":
    main()

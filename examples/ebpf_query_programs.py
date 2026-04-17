#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
import logging
import otupy as oc2
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile

from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program
from otupy.types.data.uri import URI
from otupy.types.targets.file import File

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer

import otupy.profiles.ebpf as ebpf

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

oc2.Feature.extend("clicommands", 5)


def main():
    logger.info("Creating Producer")
    p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))

    pf = ebpf.Specifiers({})
    #arg = rcli.Args({"response_requested": oc2.ResponseType.complete})
    full_path = "/opt/abba/tmacp/fcd/a/allow.o"
    direction = "ingress"
    attach_type = "tc"
    iface = "wlp7s0"
    section = "tc"
    prog = ProgramFile(full_path, Section=section,isUri=False) 
    direction_obj = Direction(direction)
    attach_obj = AttachType(attach_type)
    interfaces = Interfaces(iface)
    target_features = eBPF_program(file=None)
    #storage= File({"path": "tmacp/fcd/a", "name": "allow.o"})
    args = ebpf.Args({"Direction": direction_obj, "AttachType": attach_obj, "Interfaces": interfaces})
    cmd = oc2.Command(oc2.Actions.query,target=target_features,args=None, actuator=pf)

    logger.info("Sending command: %s", cmd)
    resp = p.sendcmd(cmd)
    logger.info("Got response: %s", resp)


if __name__ == "__main__":
    main()

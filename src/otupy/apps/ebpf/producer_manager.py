# ebpf_producer_utils.py
import json
import os
import logging
import otupy as oc2
from otupy.encoders.json import JSONEncoder
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.transfers.http import HTTPTransfer
from otupy.transfers.http.message import Message
from otupy.profiles.ebpf.actuator import Specifiers
from otupy.profiles.ebpf.targets.eBPF_load_TCprogram import eBPF_load_TCprogram
from otupy.profiles.ebpf.targets.eBPF_load_XDPProgram import eBPF_load_XDPProgram
from otupy.profiles.ebpf.targets.eBPF_query import eBPF_query
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.profile import Profile

logger = logging.getLogger("ebpf_producer")
logger.setLevel(logging.INFO)

# -----------------------------
# Helper: print table nicely
# -----------------------------
def print_programs_table(programs: list[dict]):
    headers = ["INTERFACE", "ATTACH_TYPE", "DIRECTION", "PROGRAM", "SECTION"]
    print(f"{headers[0]:<12} {headers[1]:<12} {headers[2]:<12} {headers[3]:<20} {headers[4]}")
    print("-" * 70)
    for p in programs:
        iface = p.get("interface", "N/A")
        attach = p.get("attach_type", "N/A")
        direction = p.get("direction", "N/A")
        prog = p.get("program", "N/A")
        section = p.get("section", "N/A")
        print(f"{iface:<12} {attach:<12} {direction:<12} {prog:<20} {section}")
def handle_response(resp):
    """
    Validate OpenC2 response.
    Raises RuntimeError if status is not OK.
    Returns parsed response body.
    """
    m = Message()
    m.set(resp)
    data = JSONEncoder().encode(m)

    try:
        parsed_data = oc2.loads(data)
        status = parsed_data['body']['openc2']['response']['status']
        status_text = parsed_data['body']['openc2']['response']['status_text']

    except AttributeError:
        parsed_data = json.loads(data)
        status = parsed_data['body']['openc2']['response']['status']
        status_text = parsed_data['body']['openc2']['response']['status_text']



    if status != 200:
        logger.error("OpenC2 command failed: %s", status_text )
        raise RuntimeError(f"OpenC2 command failed: {status_text }")

    return parsed_data

# -----------------------------
# Producer instance
# -----------------------------
def create_producer(host="127.0.0.1", port=8080, name="producer") -> oc2.Producer:
    return oc2.Producer(name, JSONEncoder(), HTTPTransfer(host, port))

# -----------------------------
# Function: load eBPF program
# -----------------------------
def load_program(producer: oc2.Producer, asset_id:str, program_path: str, iface: str, 
                 direction="ingress", attach_type="tc"):
    if not asset_id:
        raise ValueError("Asset id must be provided")

    full_path = os.path.abspath(program_path)
    prog = ProgramFile(full_path, Section="main")
    direction_obj = Direction(direction)
    attach_obj = AttachType(attach_type)
    actuator_spec = Specifiers({"asset_id": asset_id})
    target_features = eBPF_load_TCprogram(
        file=prog,
        direction=direction_obj,
        attach_type=attach_obj
    )

    cmd = oc2.Command(
        action=oc2.Actions.create,
        target=target_features,
        actuator=actuator_spec
    )

    logger.info("Sending load command for program %s on interface %s", full_path, iface)
    resp = producer.sendcmd(cmd)
    return handle_response(resp)

# -----------------------------
# Function: delete eBPF program
# -----------------------------
def delete_program(producer: oc2.Producer, asset_id:str, program_path: str, iface: str,
                   direction:str, attach_type:str):
    if not asset_id:
        raise ValueError("Asset id must be provided")

    full_path = os.path.abspath(program_path)
    prog = ProgramFile(full_path, Section="main")  # TODO: Section could be parameterized
    direction_obj = Direction(direction)
    attach_obj = AttachType(attach_type)
    interfaces = Interfaces(iface)
    actuator_spec = Specifiers({"asset_id": asset_id})
    target_features = eBPF_query(
        file=prog,
        direction=direction_obj,
        attach_type=attach_obj,
        interfaces=interfaces
    )

    cmd = oc2.Command(
        action=oc2.Actions.delete,
        target=target_features,
        actuator=actuator_spec
    )

    logger.info("Sending delete command for program %s on interface %s", full_path, iface)
    resp = producer.sendcmd(cmd)
    return handle_response(resp)

# -----------------------------
# Function: query loaded programs
# -----------------------------
def query_programs(producer: oc2.Producer, asset_id: str):
    if not asset_id:
        raise ValueError("Asset id must be provided")

    actuator_spec = Specifiers({"asset_id": asset_id})
    target_query = eBPF_query()
    cmd = oc2.Command(
        action=oc2.Actions.query,
        target=target_query,
        actuator=actuator_spec
    )

    logger.info("Sending query command")
    resp = producer.sendcmd(cmd)
    body = handle_response(resp)

    result = body.get('response', {}).get('results', {}).get(Profile.nsid, [])
    if not result:
        print("No eBPF programs loaded.")
        return []

    programs = []
    for i, prog in enumerate(result.get("Program", [])):
        iface = result.get("Interfaces", [])[i]["Names"][0] if i < len(result.get("Interfaces", [])) else "N/A"
        attach = result.get("hook_point", [])[i]["Name"] if i < len(result.get("hook_point", [])) else "N/A"
        direction = result.get("Direction", [])[i]["Name"] if i < len(result.get("Direction", [])) else "N/A"

        programs.append({
            "interface": iface,
            "attach_type": attach,
            "direction": direction,
            "program": prog["Name"],
            "section": prog.get("Section", "N/A")
        })

    print_programs_table(programs)
    return programs

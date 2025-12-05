import logging
import os
import sys
import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.profiles.ebpf.actuator import Specifiers as EbpfSpecifiers
from otupy.profiles.ebpf.targets.eBPFload_target import eBPFload_file_target
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('openc2producer')

def main():
    logger.info("Starting eBPF Producer (dry run)")

    # 1. Define eBPF Actuator Specifiers
    asset_id = 'test'
    pf = EbpfSpecifiers({'asset_id': asset_id})
    pf.fieldtypes['asset_id'] = asset_id

    # 2. Prepare eBPF program, direction, and attach type
    bpf_program = "./src/otupy/apps/ebpf/allow_all.o"
    full_path_bpf_program = os.path.abspath(bpf_program)
    prog = ProgramFile(full_path_bpf_program, Section="main")
    direction = Direction("ingress")
    attach_type = AttachType("tc")

    target_features = eBPFload_file_target(
        file=prog,
        direction=direction,
        attach_type=attach_type
    )
    

    # 3. Build OpenC2 Command
    cmd = oc2.Command(
        action=oc2.Actions.create,
        target=target_features,
        actuator=pf
    )

    # 4. Serialize to JSON for inspection (without sending)
    encoder = JSONEncoder()
    try:
        json_cmd = encoder.encode(cmd)
        logger.info("Serialized OpenC2 command (dry run):\n%s", json_cmd)
    except Exception as e:
        logger.error("Failed to encode command: %s", e)

    # Optional: print to stdout
    print(json_cmd)

if __name__ == '__main__':
    main()


import logging
import sys
import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.profiles.ctxd.data.name import Name
from otupy.transfers.http import HTTPTransfer

import otupy.profiles.ebpf as ebpf 
from otupy.profiles.ebpf.actuator import Specifiers as EbpfSpecifiers
from otupy.profiles.ebpf.targets.ebpf_program import ebpf_program
from otupy.types.base.array_of import ArrayOf
from otupy.types.targets.features import Features

logging.basicConfig(stream=sys.stdout,level=logging.INFO)
logger = logging.getLogger('openc2producer')

def main():
    logger.info("Starting eBPF Producer")
    
    # 1. Initialize Producer (come prima)
    p = oc2.Producer(
        "producer", 
        JSONEncoder(), 
        HTTPTransfer("127.0.0.1", 8080)
    )

    # 2. Define the eBPF Actuator (come prima)
    logger.info("Defining eBPF Actuator Specifiers")
    asset_id = 'test'
    pf = EbpfSpecifiers({'asset_id':asset_id})
    pf.fieldtypes['asset_id'] = asset_id

    # 3. Define Command Target: Target Features (la forma corretta per query generica)
    # L'istanza è vuota, per ottenere la serializzazione corretta (probabilmente {"features": {}} o {"features": null})
    source_file = "source_code.c"
    hook_point = "execve"
    target_features = ebpf_program(file_path=ArrayOf(Name)(source_file),prog_type=ArrayOf(Name)(hook_point)) 

    #target_features = Features()
    # 4. Crea e Invia il Comando
    cmd = oc2.Command(
        action=oc2.Actions.create, 
        target=target_features, # Usa il Target Features generico
        actuator=pf
    )
    logger.info("Sending command: %s", cmd)

    resp = p.sendcmd(cmd) 

    logger.info("Got response: %s", resp)

if __name__ == '__main__':
    main()
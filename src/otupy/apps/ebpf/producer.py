from otupy.apps.ebpf.producerManager import create_producer, load_program, query_programs

# Create producer
p = create_producer()

#The asset id to identify the test consumer
assetid = "ebpfTest1"

# Load a program
load_program(p, program_path="./src/otupy/apps/ebpf/allow_all.o", asset_id=assetid,iface="wlp7s0")

# Query programs and print nicely
query_programs(p,asset_id=assetid)

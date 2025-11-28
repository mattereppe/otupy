""" eBPF Profile Definition

    This modules contains the definition of the `ebpf` profile. It defines the nsid 
    and unique name for the eBPF profile.
"""
import otupy as oc2

# Define the namespace identifier
nsid = 'x-ebpf'

@oc2.extension(nsid = nsid)
class Profile(oc2.Profile):
    
    """ eBPF Profile

        Defines the namespace identifier and the name of the eBPF Actuator Profile.
    """
    nsid = nsid
    
    name = 'eBarkleyPacketFilter' 

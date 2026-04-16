""" eBPF Actuator Specifiers

    Define the set of specifiers to uniquely identify and target a specific eBPF 
    runtime environment (Actuator) in a system.
"""
import otupy as oc2

# Import the base Profile definition
from otupy.profiles.ebpf.profile import Profile

@oc2.actuator(nsid=Profile.nsid)
class Specifiers(oc2.Map):

    fieldtypes = dict(domain=str, asset_id=str)
    def __init__(self,dic):
        """ Initialize the `Specifiers` map for the eBPF profile """
        self.nsid = Profile.nsid
        oc2.Map.__init__(self, dic)
    
    def __str__(self):
        id = self.nsid + '('
        for k,v in self.items():
            id += str(k) + ':' + str(v) + ','
        id = id.strip(',')
        id += ')'
        return id
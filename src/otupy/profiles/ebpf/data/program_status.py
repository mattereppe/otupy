""" eBPF Program Status
"""
import otupy as oc2

from otupy.profiles.ebpf.data.map_ebpf import MapeBPF
from otupy.profiles.ebpf.profile import Profile
from otupy.types.base.array_of import ArrayOf
from otupy.types.base.map_of import MapOf
from otupy.types.base.record import Record
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile

@oc2.extension(nsid=Profile.nsid)
class ProgramStatus(oc2.Results):

	fieldtypes = {'Program': ProgramFile, 'Direction': Direction, 'hook_point': AttachType, 
			   'Interfaces': Interfaces,
			   'maps': ArrayOf(MapeBPF)
			   }

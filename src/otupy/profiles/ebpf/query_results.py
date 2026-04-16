""" CTXD Response extensions

"""
import otupy as oc2

from otupy.profiles.ebpf.profile import Profile
from otupy.types.base.array_of import ArrayOf
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile

@oc2.extension(nsid=Profile.nsid)
class QueryResults(oc2.Results):

	fieldtypes = {'Program': ArrayOf(ProgramFile), 'Direction': ArrayOf(Direction), 'hook_point': ArrayOf(AttachType), 
			   'Interfaces': ArrayOf(Interfaces)}


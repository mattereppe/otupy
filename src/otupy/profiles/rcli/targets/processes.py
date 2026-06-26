from otupy.types.base import ArrayOf
from otupy.profiles.rcli.data.process import Process
from otupy.core.target import target
from otupy.profiles.rcli.profile import Profile  # Assuming this exists


@target(name="processes", nsid=Profile.nsid)
class Processes(ArrayOf(Process)):
    """OpenC2 processes

    Implements the `processes` target (Section 3.4.1.5).
    Just defines an `ArrayOf` `Feature`.
    """

    def __init__(self, procs=[]):
        super().__init__(procs)
        self.validate(types=True, num_max=10)

from otupy.types.base import Record
from otupy.types.base.enumerated import Enumerated


class AttachType(Enumerated):
    """
    OpenC2-compliant enum representing the eBPF attach type.
    Allowed values: "tc", "xdp"
    """

    tc = 1
    """ Attach to Traffic Control (TC) """
    xdp = 2
    """ Attach to eXpress Data Path (XDP) """


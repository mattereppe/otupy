from __future__ import annotations
from otupy.types.base import Record
from otupy.types.base import Enumerated

class Direction(Enumerated):
    """
    OpenC2-compliant enum for packet direction in eBPF (TC/XDP).
    Allowed values: "ingress", "egress", "both"
    """

    ingress = 1
    """ Apply rules to incoming traffic only """
    egress = 2
    """ Apply rules to outgoing traffic only """
    both = 3
    """ Apply rules to all traffic """
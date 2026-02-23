from otupy.types.base import Enumerated

class LinkType(Enumerated):
    """Link-Type

    type of the link
    """

    api = 1
    hosting = 2
    packet_flow = 3
    controlling = 4
    protecting = 5
    containing = 6
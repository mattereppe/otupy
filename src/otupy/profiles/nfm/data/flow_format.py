from otupy.types.base import Enumerated


class FlowFormat(Enumerated):
    """Flow Format

    format of the flow
    """

    netflow5 = 1
    netflow7 = 2
    netflow9 = 3
    ipfix = 4
    json = 5
    csv = 6

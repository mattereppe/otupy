import otupy as oc2
from otupy.profiles.nfm.profile import Profile  # Assuming this exists
from otupy.types.base import ArrayOf, Array
from otupy.types.targets import IPv4Connection, IPv6Connection


# Target for FlowMonitor Configuration
@oc2.target(name="monitor", nsid=Profile.nsid)
class FlowMonitor(oc2.types.base.Record):
    """
    FlowMonitor

    Represents a monitoring system capable of handling flow data.
    """


    filter_v4: ArrayOf(IPv4Connection) = None  # type: ignore
    """ List of IPv4 addresses assigned to the interface (including prefix) """

    filter_v6: ArrayOf(IPv6Connection) = None  # type: ignore
    """ List of IPv6 addresses assigned to the interface (including prefix) """

    def __init__(
        self,
        filter_v4: ArrayOf = None,
        filter_v6: ArrayOf = None,
    ):  # type: ignore
        if isinstance(filter_v4, FlowMonitor):
            self._init_from_flowmonitor(filter_v4)
        else:
            self._init_from_params(filter_v4, filter_v6)
        self.validate_fields()

    def _init_from_flowmonitor(self, flowmonitor):
        self.filter_v4 = flowmonitor.filter_v4
        self.filter_v6 = flowmonitor.filter_v6

    def _init_from_params(self, filter_v4, filter_v6):
        self.filter_v4 = filter_v4
        self.filter_v6 = filter_v6

    def __repr__(self):
        return (
            f"FlowMonitor(filter_v4={self.filter_v4}, filter_v6={self.filter_v6})"
        )

    def __str__(self):
        return self.__repr__()

    def validate_fields(self):

        if self.filter_v4 is not None and not isinstance(self.filter_v4, Array):
            raise TypeError(f"'filter_v4' must be ArrayOf(IPv4Addr), got {type(self.filter_v4)}")
        if self.filter_v6 is not None and not isinstance(self.filter_v6, Array):
            raise TypeError(f"'filter_v6' must be ArrayOf(IPv6Addr), got {type(self.filter_v6)}")

    def get(self, key, default=None):
        """Mimics dictionary get method"""
        return getattr(self, key, default)

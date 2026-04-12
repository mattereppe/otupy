import otupy as oc2
from otupy.profiles.fclm.profile import Profile  # Assuming this exists
from otupy.types.base import ArrayOf, Array
from otupy.types.targets import File, URI
from otupy.profiles.fclm.data.socket import Socket
from otupy.types.base import Choice
from otupy.types.data.hostname import Hostname
from otupy.types.targets.ipv4_connection import IPv4Connection
from otupy.core.register import Register


# Target for LogMonitor Configuration
@oc2.target(name="monitor", nsid=Profile.nsid)
class LogMonitor(Choice):
    """
    LogMonitor

    Represents a file log monitoring system. Suitable for agents that collect logs
    from files, URIs, or sockets and attach metadata.
    """

    register = Register({"file": File, "URI": URI, "socket": Socket})

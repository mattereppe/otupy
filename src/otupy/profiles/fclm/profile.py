"""File Collection Log Monitor namespace

This module defines the nsid and unique name for the FCLM profile.
No explicit values are used anywhere in the rest of the code.
"""

from otupy import Profile, extension

nsid = "x-fclm"


@extension(nsid=nsid)
class Profile(Profile):
    """FCLM Profile

    Defines the namespace identifier and the name of the FCLM Profile.
    """

    nsid = nsid
    name = "File Collecion Log Monitoring"

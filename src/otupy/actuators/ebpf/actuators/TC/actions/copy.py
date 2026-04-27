import os
import logging
from otupy.core.command import Command
from otupy.core.response import Response
from otupy.actuators.rcli.actions.copy import copy as rcli_copy
logger = logging.getLogger(__name__)


def copy(cmd: Command) -> Response:
    
    return rcli_copy(cmd)
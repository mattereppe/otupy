"""Skeleton `Actuator` for RCLI profile

This module provides an example to create an `Actuator` for the RCLI profile.
It only answers to the request for available features.
"""

import logging
from otupy import Actions, Feature, actuator_implementation
import otupy.profiles.rcli as rcli
from otupy.actuators.rcli.actions.copy import copy
from otupy.actuators.rcli.actions.delete import delete
from otupy.actuators.rcli.actions.start import start
from otupy.actuators.rcli.actions.stop import stop
from otupy.actuators.rcli.actions.query import query
from otupy.actuators.rcli.handlers.response_handler import notimplemented, servererror, notfound
from otupy.actuators.rcli.cli.commands import Commands

logger = logging.getLogger(__name__)
#Feature.extend("clicommands", 5)


# An implementation of the rcli profile.
@actuator_implementation("rcli-linux")
class RCLIActuator:
    """RCLI implementation

    This class provides an implementation of the RCLI `Actuator`.
    """

    def __init__(self, *, specifiers, **kwargs):
        """Initialization of the `RCLI Actuator`.
			  Assign default values; always call this before any specific initialization of derived classes.

        :param asset_id: RCLI Actuator asset id.
        """
        self.asset_id = specifiers["asset_id"]
        self.file_location = kwargs.get('file_location', '/tmp')
        Commands.load_allowed_commands( kwargs.get('allowed_commands', {}) )

    def run(self, cmd):
        logger.info(f"Received command for processing: {cmd}")
        if not rcli.validate_command(cmd):
            return notimplemented("Invalid Action/Target pair")
        if not rcli.validate_args(cmd):
            return notimplemented("Argument not supported")
        # Check if the Specifiers are actually served by this Actuator
        try:
            if not self.__is_addressed_to_actuator(cmd.actuator.getObj()):
                return notfound("Requested Actuator not available")
        except AttributeError:
            # If no actuator is given, execute the command
            pass
        except Exception as e:
            return servererror("Unable to identify actuator", e)
        try:
            match cmd.action:
                case Actions.query:
                    response = query(cmd)
                case Actions.start:
                    response = start(cmd)
                case Actions.stop:
                    response = stop(cmd)
                case Actions.copy:
                    response = copy(cmd, self.file_location)
                case Actions.delete:
                    response = delete(cmd, self.file_location)
                case _:
                    response = notimplemented("Command not implemented")
        except Exception as e:
            return servererror("Server error while processing command", e)

        logger.info(f"Response generated: {response}")
        return response

    def __is_addressed_to_actuator(self, actuator):
        """Checks if this Actuator must run the command"""
        if len(actuator) == 0:
            # Empty specifier: run the command
            return True
        for k, v in actuator.items():
            try:
                if v == self.asset_id:
                    return True
            except KeyError:
                pass
        return False

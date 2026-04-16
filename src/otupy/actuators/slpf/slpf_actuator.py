"""Base class for the SLPF actuators."""

import atexit
import hashlib
import logging
import os
import threading
import time
import uuid
from abc import ABC
from datetime import datetime
from enum import Enum

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

import otupy.profiles.slpf as slpf
from otupy import (
    ArrayOf,
    File,
    Nsid,
    Version,
    Command,
    Response,
    StatusCode,
    StatusCodeDescription,
    Features,
    ResponseType,
    Feature,
    IPv4Net,
    IPv4Connection,
    IPv6Net,
    IPv6Connection,
    DateTime,
    Duration,
    Binaryx,
    L4Protocol,
    Port,
)
from otupy.core.actions import Actions
from otupy.profiles.slpf.data import DropProcess
from .sql_database import SQLDatabase

logger = logging.getLogger(__name__)

OPENC2VERS = Version(1, 0)
""" Supported OpenC2 Version """


class SLPFActuator(ABC):
    """Base class for the SLPF actuators."""

    class Mode(Enum):
        """This class defines the operational modes of the Actuator Manager.

        In `DB Mode`, the filtering rules stored in the database through `allow` and `deny` commands are used to manage
        the actuator's behavior.

        In `FILE Mode`, the filtering rules contained in the file specified as the target of the last `update` command
        are applied to manage the actuator's behavior.
        """

        db = "Database"
        file = "File"

    def __init__(
        self,
        asset_id=None,
        db_path=None,
        db_name=None,
        db_commands_table_name=None,
        db_jobs_table_name=None,
        update_path=None,
        **kwargs,
    ):
        """Initialization of the `SLPF Actuator Manager`.

        Initializes an `sqlite3` database to store `allow` and `deny` OpenC2 Commands,
        as well as `APScheduler jobs` for commands that have not been executed (in case of a shutdown of the SLPF
        Actuator Manager).
        It checks the current `SLPF Actuator Manager Mode` (either `DB mode` or `FILE mode`),
        restores `persistent` OpenC2 Commands,
        and initializes an `APScheduler scheduler` to manage commands scheduled for specific `start time` or `stop time`.
        Finally it registers the `slpf_exit()` method to be executed during the `shutdown` of the SLPF Actuator Manager.

        :param asset_id: SLPF Actuator asset id.
        :type asset_id: str
        :param db_path: sqlite3 database directory path.
        :type db_path: str
        :param db_name: sqlite3 database name.
        :type db_name: str
        :param db_commands_table_name: Name of the `OpenC2 Commands` table in the sqlite3 database.
        :type db_commands_table_name: str
        :param db_jobs_table_name: Name of the `APScheduler jobs` table in the sqlite3 database.
        :type db_jobs_table_name: str
        :param update_path: Path to the default directory containing files to be used as update.
        :type update_path: str
        """
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.tag = "[SLPF-" + asset_id + "]"

            try:
                #   Path where update files are stored
                self.update_directory_path = update_path if update_path else os.path.dirname(os.path.abspath(__file__))
                if not os.path.exists(self.update_directory_path):
                    raise ValueError("Update directory path does not exists")
                #   Initializing database
                logger.info(self.tag + " Initializing database")
                self.db_directory_path = db_path if db_path else os.path.dirname(os.path.abspath(__file__))
                self.db_name = db_name if db_name else "slpf_commands.sqlite"
                if not os.path.exists(self.db_directory_path):
                    raise ValueError("Database directory path does not exists")
                self.db_commands_table_name = db_commands_table_name
                self.db_jobs_table_name = db_jobs_table_name
                self.db = SQLDatabase(
                    os.path.join(self.db_directory_path, self.db_name),
                    self.db_commands_table_name,
                    self.db_jobs_table_name,
                )
                #   Checking SLPF Mode
                self.mode = SLPFActuator.Mode.file if self.db.is_empty() else SLPFActuator.Mode.db
                logger.info(self.tag + " " + self.mode.value + " mode")
                #   Restoring persistent commands
                self.restore_persistent_commands()
                #   Initializing scheduler
                logger.info(self.tag + " Initializing scheduler")
                # Setting misfire grace time to 1 day
                self.misfire_grace_time = 86400
                self.scheduler = BackgroundScheduler(executors={"default": ThreadPoolExecutor(max_workers=1)})
                self.scheduler.add_listener(
                    lambda event: self.scheduler_listener(event), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
                )
                self.restore_persistent_jobs()
                self.scheduler.start()
                #   Registering exit function
                atexit.register(self.slpf_exit)
                logger.info(self.tag + " Initialization executed successfully")
            except Exception as e:
                logger.info(self.tag + " Initialization error: %s", str(e))
                raise e

    def execute_allow_command(self, target, direction, custom_data):
        """Implementation of `allow` action

        Each Actuator must override this method to implement the `allow` action in its specific environment.

        :param target: The target of the allow action.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to allow incoming traffic, outgoing traffic or both for the specified target.
        :type direction: Direction
        :param custom_data: Contains custom data specific to this actuator, previously stored in the database.
        :type custom_data: dict
        """
        pass

    def execute_deny_command(self, target, direction, drop_process, custom_data):
        """Implementation of `deny` action

        Each Actuator must override this method to implement the `deny` action in its specific environment.

        :param target: The target of the deny action.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param direction: Specifies whether to deny incoming traffic, outgoing traffic or both for the specified target.
        :type direction: Direction
        :param drop_process: Specifies how to handle denied packets.
        :type drop_process: DropProcess
        :param custom_data: Contains custom data specific to this actuator, previously stored in the database.
        :type custom_data: dict
        """
        pass

    def validate_action_target_args(self, action, target, args):
        """This method should be implemented to validate SLPF `actions` and `targets`, as well as the `direction` and `drop_process` arguments in the specific actuator environment,
        or to perform additional checks before executing an action (e.g: check if the file extension of an update target is supported).

        It may also return actuator-specific custom data, which will be stored in the database and used during the future execution of the function.

        Possibles `action` values are `allow`, `deny` and `update`, since query and delete action are already fully validated.

        This method should validates `Target` and `Args` of an `allow` action for a specific Actuator.

        This method should validates `Target` and `Args` of a `deny` action for a specific Actuator.

        This method should validates `Target` of an `update` action for a specific Actuator, since `Args` are already fully validated.

        :param action: The action to validate.
        :type action: Actions
        :param target: The target of the action to validate.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection/File
        :param args: The arguments of the action to validate.
                    Contains the direction argument in case of `allow` action,
                    the direction and drop_process arguments in case of `deny` action
                    and has a None value in case of `update` action.
        :type args: slpf.Args

        :return: Optional actuator-specific custom data to be stored in the database for future function execution
        :rtype: dict
        """
        pass

    def execute_delete_command(self, command_to_delete, custom_data):
        """Implementation of `delete` action

        Each Actuator must override this method to implement the `delete` action in its specific environment.

        :param command_to_delete: The OpenC2 Command to delete.
        :type command_to_delete: Command
        :param custom_data: Contains custom data specific to this actuator, previously stored in the database.
        :type custom_data: dict
        """
        pass

    def execute_update_command(self, name, path):
        """Implementation of `update` action

        Each Actuator must override this method to implement the `delete` action in its specific environment.

        :param name: The `name` of the target file.
        :type name: str
        :param path: The `path` of the target file.
        :type path: str
        """
        pass

    def save_persistent_commands(self):
        """Each Actuator must override this method to `save` all active commands in its specific environment."""
        pass

    def restore_persistent_commands(self):
        """Each Actuator must override this method to `restore` all commands previously saved using the save_persistent_commands() method, in its specific environment."""
        pass

    def clean_actuator_rules(self):
        """Each Actuator must override this method to `remove all rules` in its environment,
        in response to a change in the Actuator Manager's mode (from DB mode to FILE mode, or vice versa).
        """
        pass

    def run(self, cmd):
        # Check if the Command is compliant with the implemented profile
        if not slpf.validate_command(cmd):
            return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Invalid Action/Target pair")
        if not slpf.validate_args(cmd):
            return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Option not supported")

        # Check if the Specifiers are actually served by this Actuator
        try:
            if not self.__is_addressed_to_actuator(cmd.actuator.getObj()):
                return Response(status=StatusCode.NOTFOUND, status_text="Requested Actuator not available")
        except AttributeError:
            # If no actuator is given, execute the command
            pass
        except Exception as e:
            return Response(status=StatusCode.INTERNALERROR, status_text="Unable to identify actuator")

        try:
            match cmd.action:
                case Actions.query:
                    response = self.query(cmd)
                case Actions.allow:
                    response = self.allow(cmd)
                case Actions.deny:
                    response = self.deny(cmd)
                case Actions.update:
                    response = self.update(cmd)
                case Actions.delete:
                    response = self.delete(cmd)
                case _:
                    response = self.__notimplemented(cmd)
        except Exception as e:
            return self.__servererror(cmd, e)

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

    def query(self, cmd):
        """`Query` action

        This method provides a default and complete implementation of the `query` action.

        :param cmd: The OpenC2 Command including `Target` and optional `Args`.
        :type cmd: Command

        :return: An OpenC2 Response including the result of the query command and an appropriate status code and description.
        :rtype: Response
        """

        # Sec. 4.1 Implementation of the 'query features' command
        if cmd.args is not None:
            if len(cmd.args) > 1:
                return Response(satus=StatusCode.BADREQUEST, statust_text="Invalid query argument")
            if len(cmd.args) == 1:
                try:
                    if cmd.args["response_requested"] != ResponseType.complete:
                        raise KeyError
                except KeyError:
                    return Response(status=StatusCode.BADREQUEST, status_text="Invalid query argument")

        if cmd.target.getObj().__class__ == Features:
            r = self.query_feature(cmd)
        else:
            return Response(
                status=StatusCode.BADREQUEST, status_text="Querying " + cmd.target.getName() + " not supported"
            )

        return r

    def query_feature(self, cmd):
        """Query features

        Implements the 'query features' command according to the requirements in Sec. 4.1 of the Language Specification.

        Each Actuator must override this method if it does not implement a specific feature in its environment.
        """

        features = {}
        for f in cmd.target.getObj():
            match f:
                case Feature.versions:
                    features[Feature.versions.name] = ArrayOf(Version)([OPENC2VERS])
                case Feature.profiles:
                    pf = ArrayOf(Nsid)()
                    pf.append(Nsid(slpf.Profile.nsid))
                    features[Feature.profiles.name] = pf
                case Feature.pairs:
                    features[Feature.pairs.name] = slpf.AllowedCommandTarget
                case Feature.rate_limit:
                    return Response(
                        status=StatusCode.NOTIMPLEMENTED, status_text="Feature 'rate_limit' not yet implemented"
                    )
                case _:
                    return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Invalid feature '" + f + "'")

        res = None
        try:
            res = slpf.Results(features)
        except Exception as e:
            return self.__servererror(cmd, e)

        return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=res)

    def allow(self, cmd):
        """`Allow` action

        This method implements the `allow` action.

        :param cmd: The OpenC2 Command including `Target` and optional `Args`.
        :type cmd: Command

        :return: An OpenC2 Response including the result of the allow command and an appropriate status code and description.
        :rtype: Response
        """

        try:
            return self.allow_deny_handler(cmd)
        except Exception as e:
            return self.__servererror(cmd, e)

    def deny(self, cmd):
        """`Deny` action

        This method implements the `deny` action.

        :param cmd: The OpenC2 Command including `Target` and optional `Args`.
        :type cmd: Command

        :return: An OpenC2 Response including the result of the deny command and an appropriate status code and description.
        :rtype: Response
        """

        try:
            return self.allow_deny_handler(cmd)
        except Exception as e:
            return self.__servererror(cmd, e)

    def allow_deny_handler(self, cmd):
        """This method manages the execution of `allow` and `deny` commands.

        It validates `Target` and `Args` of the command according to the OpenC2 SLPF Specification,
        It applies default values for any unspecified arguments and performs actuator-specific validation through the
        `validate_action_target_arguments` method (which must be overridden by the actuator).
        It also retrieves any actuator-specific `custom_data` to be stored.
        If the system is currently operating in `FILE mode`, it switches the SLPF Actuator Manager to `DB mode` (database rules in use).
        It then inserts the OpenC2 command into the `database`, together with the associated `custom_data`,
        and schedules the command to be executed at the specific `start` time,
        while ensuring its effect is cancelled at the specified `stop` time (if provided).

        :param cmd: The OpenC2 Command including `Target` and optional `Args`.
        :type cmd: Command

        :return: An OpenC2 Response including the result of the allow or deny command and an appropriate status code and description.
        :rtype: Response
        """

        try:
            action = cmd.action
            target = cmd.target.getObj()
            args = cmd.args

            #   Validating target
            if (
                type(target) != IPv4Net
                and type(target) != IPv6Net
                and type(target) != IPv4Connection
                and type(target) != IPv6Connection
            ):
                raise TypeError("Invalid target type")
            if type(target) == IPv4Connection or type(target) == IPv6Connection:
                if (
                    target.protocol
                    and target.protocol != L4Protocol.tcp
                    and target.protocol != L4Protocol.udp
                    and target.protocol != L4Protocol.sctp
                ):
                    if target.src_port or target.dst_port:
                        raise ValueError(
                            StatusCode.BADREQUEST, "Source/Destination port not supported with provided protocol"
                        )
                if not target.protocol and (target.src_port or target.dst_port):
                    raise ValueError(StatusCode.BADREQUEST, "Protocol must be provided")

                addr_type = IPv4Net if type(target) == IPv4Connection else IPv6Net
                if (
                    (target.src_addr and type(target.src_addr) != addr_type)
                    or (target.dst_addr and type(target.dst_addr) != addr_type)
                    or (target.protocol and type(target.protocol) != L4Protocol)
                    or (target.src_port and type(target.src_port) != Port)
                    or (target.dst_port and type(target.dst_port) != Port)
                ):
                    raise TypeError("Invalid target type")

            #   Validating args
            if (
                ("response_requested" in args and type(args["response_requested"]) != ResponseType)
                or ("insert_rule" in args and type(args["insert_rule"]) != slpf.RuleID)
                or ("direction" in args and type(args["direction"]) != slpf.Direction)
                or ("persistent" in args and type(args["persistent"]) != bool)
                or ("drop_process" in args and type(args["drop_process"]) != DropProcess)
                or ("start_time" in args and type(args["start_time"]) != DateTime)
                or ("stop_time" in args and type(args["stop_time"]) != DateTime)
                or ("duration" in args and type(args["duration"]) != Duration)
            ):
                tmp_str = "Invalid allow argument type" if action == Actions.allow else "Invalid deny argument type"
                raise TypeError(tmp_str)

            if "insert_rule" in args:
                if not "response_requested" in args or args["response_requested"] != ResponseType.complete:
                    raise ValueError(
                        StatusCode.BADREQUEST, "Response requested must be complete with insert rule argument"
                    )
                if self.db.find_command(args["insert_rule"]):
                    raise ValueError(StatusCode.NOTIMPLEMENTED, "Rule number currently in use")

            if ("start_time" in args) and ("stop_time" in args):
                if "duration" in args:
                    raise ValueError(
                        StatusCode.BADREQUEST,
                        "Only two arguments between start time, stop time and duration can be specified",
                    )
                if args["start_time"] > args["stop_time"]:
                    raise ValueError(StatusCode.BADREQUEST, "Start time greater than stop time")

            #   Setting default args values
            if not "direction" in args:
                args["direction"] = slpf.Direction.both
            if action == Actions.deny and not "drop_process" in args:
                args["drop_process"] = DropProcess.none

            #   Actuator-specific arguments
            temp_args = {"direction": args["direction"]}
            if "drop_process" in args:
                temp_args["drop_process"] = args["drop_process"]

            #   Validating action, target and args in the specific actuator environment
            #   and retrieving any possible custom data to store in the database.
            custom_data = self.validate_action_target_args(action=action, target=target, args=temp_args)

            #   If stop time already expired, OK without rule number is returned
            if "stop_time" in args and (args["stop_time"] <= time.time() * 1000):
                return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK])

            #   Calculating start/stop time
            if "start_time" in args:
                args["start_time"] = args["start_time"] / 1000
            else:
                if "stop_time" in args and "duration" in args:
                    args["start_time"] = (args["stop_time"] - args["duration"]) / 1000
                else:
                    args["start_time"] = time.time()
            if "stop_time" in args:
                args["stop_time"] = args["stop_time"] / 1000
            else:
                if "duration" in args:
                    args["stop_time"] = (args["start_time"] * 1000 + args["duration"]) / 1000

            if self.mode == SLPFActuator.Mode.file:
                #   Setting SLPF Actuator Manager in DB Mode
                self.mode = SLPFActuator.Mode.db
                logger.info(self.tag + " " + self.mode.value + " mode setted")
                #   Cleaning all rules in the specific actuator environment (starting to use db rules)
                self.clean_actuator_rules()
                self.save_persistent_commands()

            #   Generating scheduler job IDs
            scheduler_data = {
                "start_job_id": self.generate_unique_job_id(),
                "stop_job_id": self.generate_unique_job_id() if "stop_time" in args else None,
            }

            #   Inserting the OpenC2 command and custom data into the database
            logger.info(self.tag + " Inserting command in database")
            rule_number = self.db_handler(action, target, args, custom_data, scheduler_data)

            #   Managing the scheduler
            scheduler_data["my_id"] = None
            start_time = datetime.fromtimestamp(args["start_time"])
            self.scheduler.add_job(
                self.allow_deny_execution_wrapper,
                "date",
                next_run_time=start_time,
                args=[action, rule_number],
                kwargs={"target": target, "custom_data": custom_data, **temp_args},
                id=scheduler_data["start_job_id"],
                misfire_grace_time=self.misfire_grace_time,
            )
            if "stop_time" in args:
                command = Command(action, target, slpf.Args(temp_args))
                scheduler_data["my_id"] = scheduler_data["stop_job_id"]
                stop_time = datetime.fromtimestamp(args["stop_time"])
                self.scheduler.add_job(
                    self.delete_handler,
                    "date",
                    next_run_time=stop_time,
                    kwargs={
                        "command_to_delete": command,
                        "rule_number": rule_number,
                        "custom_data": custom_data,
                        "scheduler_data": scheduler_data,
                    },
                    id=scheduler_data["stop_job_id"],
                    misfire_grace_time=self.misfire_grace_time,
                )

            res = slpf.Results(rule_number=slpf.RuleID(rule_number))
            return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK], results=res)
        except TypeError as e:
            return Response(status=StatusCode.BADREQUEST, status_text=str(e))
        except ValueError as e:
            return Response(status=e.args[0], status_text=e.args[1])
        except Exception as e:
            return Response(status=StatusCode.INTERNALERROR, status_text="Rule not updated")

    def allow_deny_execution_wrapper(self, *args, **kwargs):
        """This method is a wrapper for the execution of `allow` and `deny` commands in the specific SLPF Actuator environment.

        :param args: Contains the `Action` to be executed (allow or deny) and the `rule number` assigned to this rule.
        :type args: list
        :param kwargs: A dictionary of actuator-specific arguments
        :type kwargs: dict
        """

        try:
            #   Executing allow/deny command in the specific SLPF Actuator environment
            function = self.execute_allow_command if args[0] == Actions.allow else self.execute_deny_command
            function(**kwargs)
            logger.info(self.tag + " %s action executed successfully", args[0].__repr__().capitalize())
        except Exception as e:
            logger.info(self.tag + " Execution error for %s action: %s", args[0].__repr__().capitalize(), str(e))
            e.arg = {"command_action": args[0], "rule_number": args[1]}
            raise e

    def delete(self, cmd):
        """`Delete` action

        This method implements the `delete` action.

        It validates `Target` and `Args` of the command according to the OpenC2 SLPF Specification,
        gets the rule with the specified `rule number` from the `database` and recontructs it as an `OpenC2 Command`.
        Finally schedules the delete action to be executed at a specific `start time`.

        :param cmd: The OpenC2 Command including `Target` and optional `Args`.
        :type cmd: Command
        :return: An OpenC2 Response including the result of the delete command and an appropriate status code and description.
        :rtype: Response
        """

        target = cmd.target.getObj()
        args = cmd.args
        rule_number = int(target)

        try:
            #   Validating target
            if type(target) != slpf.RuleID:
                raise TypeError("Invalid target type")

                #   Validating args
            if ("response_requested" in args and type(args["response_requested"]) != ResponseType) or (
                "start_time" in args and type(args["start_time"]) != DateTime
            ):
                raise TypeError("Invalid delete argument type")

            #   Checking if the requested command is present in the database
            if not self.db.find_command(rule_number):
                raise

            #   Calculating start time
            start_time = args["start_time"] / 1000 if "start_time" in args else time.time()
            start_time = datetime.fromtimestamp(start_time)

            #   Retrieving the OpenC2 Command and associated custom data from the database
            cmd_data = self.db.get_command(rule_number)
            custom_data = cmd_data["custom_data"]
            #   Reconstructing the OpenC2 Command
            command_to_delete = self.reconstruct_command(cmd_data)

            #   Managing the scheduler
            scheduler_data = cmd_data["scheduler_data"]
            scheduler_data["my_id"] = self.generate_unique_job_id()
            self.scheduler.add_job(
                self.delete_handler,
                "date",
                next_run_time=start_time,
                kwargs={
                    "command_to_delete": command_to_delete,
                    "rule_number": rule_number,
                    "custom_data": custom_data,
                    "scheduler_data": scheduler_data,
                },
                id=scheduler_data["my_id"],
                misfire_grace_time=self.misfire_grace_time,
            )

            return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK])
        except TypeError as e:
            return Response(status=StatusCode.BADREQUEST, status_text=str(e))
        except Exception as e:
            return Response(status=StatusCode.INTERNALERROR, status_text="Firewall rule not removed or updated")

    def delete_handler(self, command_to_delete, rule_number, custom_data, scheduler_data):
        """This method manages the execution of `delete` commands.

        If the rule to be deleted is not yet active because its `start time` has not yet been reached
        or if it is scheduled to be annulled at a specific `stop time`,
        the jobs responsible for these operations are cancelled.
        If the rule to be deleted has already been annulled, this method terminates.

        Finally, it executes the delete action in the specific `SLPF Actuator environment` and
        deletes the corresponding rule from the `database`.

        This method can be executed by a `delete` command,
        an `allow` or `deny` command with a certain `stop time`
        and from the `slpf_exit()` method to delete all non persistent OpenC2 Commands at SLPF Actuator `shutdown`.

        :param command_to_delete: The OpenC2 Command that will be deleted.
        :type command_to_delete: Command
        :param rule_number: The rule number of the rule that will be deleted.
        :type rule_number: RuleID
        :param custom_data: Actuator-specific custom data associated with the rule that will be deleted.
        :type custom_data: dict
        :param scheduler_data: Contains information about `APScheduler job IDs`:
                                `start_job_id` is the ID of the job responsible to activate, at a certain `start time`, the allow or deny action,
                                `stop_job_id` is the ID of the job responsible to deactivate, at a certain `stop time`, the allow or deny action,
                                `my_id` is the ID of the job that is executing this function.
        :type scheduler_data: dict
        """

        try:
            if scheduler_data["stop_job_id"]:
                if self.scheduler.get_job(scheduler_data["stop_job_id"]):
                    #   Removing the stop job (if present)
                    self.scheduler.remove_job(scheduler_data["stop_job_id"])
                else:
                    #   An allow/deny command has set a stop time job that is no longer present in the scheduler.
                    #   Since this is a delete action (not allow or deny with a specific stop time),
                    #   the rule has already been removed and the delete action terminates.
                    if scheduler_data["my_id"] and scheduler_data["my_id"] != scheduler_data["stop_job_id"]:
                        return

            if self.scheduler.get_job(scheduler_data["start_job_id"]):
                #   Removing the start job (if present)
                #   If the start job is still present in the scheduler the rule is not yet active in the specific actuator environment,
                #   but is only saved in the database.
                #   In this case, the delete action is not executed in the specific actuator environment.
                self.scheduler.remove_job(scheduler_data["start_job_id"])
            else:
                #   If the start job is not present in the scheduler, the rule must be deleted in the specific actuator environment
                self.execute_delete_command(command_to_delete, custom_data)

            #   Deleting the OpenC2 Command from the database
            logger.info(self.tag + " Deleting command from database")
            self.db.delete_command(rule_number)

            logger.info(self.tag + " Delete action executed successfully")
        except Exception as e:
            logger.info(self.tag + " Execution error for delete action: %s", str(e))
            e.arg = {"command_action": Actions.delete}
            raise e

    def update(self, cmd):
        """`Update` action

        This method implements the `update` action.

        It validates `Target` and `Args` of the command according to the OpenC2 SLPF Specification
        and schedules the update action to be executed at a specific `start time`.

        :param cmd: The OpenC2 Command including `Target` and optional `Args`.
        :type cmd: Command

        :return: An OpenC2 Response including the result of the delete command and an appropriate status code and description.
        """

        try:
            target = cmd.target.getObj()
            args = cmd.args

            #   Validating action, target and args in the specific actuator environment
            #   No custom data is required in the update action.
            self.validate_action_target_args(action=cmd.action, target=target, args=None)

            #   Validating target
            if type(target) != File:
                raise TypeError("Invalid target type")

            if not "name" in target or not target["name"]:
                raise ValueError(StatusCode.BADREQUEST, "Target file name must be specified")
            if type(target["name"]) != str:
                raise TypeError("Invalid update argument type")

            if "path" in target and type(target["path"]) != str:
                raise TypeError("Invalid update argument type")
            path = target["path"] if "path" in target else None
            abs_path = (
                os.path.join(self.update_directory_path, target["name"]) if not "path" in target else target["path"]
            )
            if not os.path.exists(abs_path):
                raise ValueError(StatusCode.INTERNALERROR, "Cannot access file")

            if "hashes" in target:
                if "md5" in target["hashes"] and type(target["hashes"]["md5"]) != Binaryx:
                    raise TypeError("Invalid update argument type")
                if "sha1" in target["hashes"] and type(target["hashes"]["sha1"]) != Binaryx:
                    raise TypeError("Invalid update argument type")
                if "sha256" in target["hashes"] and type(target["hashes"]["sha256"]) != Binaryx:
                    raise TypeError("Invalid update argument type")

                #               Checking hashes
                md5_hash = hashlib.md5() if "md5" in target["hashes"] else None
                sha1_hash = hashlib.sha1() if "sha1" in target["hashes"] else None
                sha256_hash = hashlib.sha256() if "sha256" in target["hashes"] else None

                with open(abs_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        if md5_hash:
                            md5_hash.update(chunk)
                        if sha1_hash:
                            sha1_hash.update(chunk)
                        if sha256_hash:
                            sha256_hash.update(chunk)

                if md5_hash and Binaryx(md5_hash.hexdigest()).__str__() != target["hashes"]["md5"].__str__():
                    raise ValueError(StatusCode.BADREQUEST, "Invalid md5 hash value")
                if sha1_hash and Binaryx(sha1_hash.hexdigest()).__str__() != target["hashes"]["sha1"].__str__():
                    raise ValueError(StatusCode.BADREQUEST, "Invalid sha1 hash value")
                if sha256_hash and Binaryx(sha256_hash.hexdigest()).__str__() != target["hashes"]["sha256"].__str__():
                    raise ValueError(StatusCode.BADREQUEST, "Invalid sha256 hash value")

            #   Validating args
            if "response_requested" in args:
                if type(args["response_requested"]) != ResponseType:
                    raise TypeError("Invalid update argument type")
                if args["response_requested"] == ResponseType.status:
                    raise ValueError(StatusCode.BADREQUEST, "Response requested cannot be set to status")
            if "start_time" in args and type(args["start_time"]) != DateTime:
                raise TypeError("Invalid update argument type")

            #   Calculating start time
            start_time = args["start_time"] / 1000 if "start_time" in args else time.time()
            start_time = datetime.fromtimestamp(start_time)

            #   Managing the scheduler
            self.scheduler.add_job(
                self.update_handler,
                "date",
                next_run_time=start_time,
                kwargs={"name": target["name"], "path": abs_path},
                id=self.generate_unique_job_id(),
                misfire_grace_time=self.misfire_grace_time,
            )

            return Response(status=StatusCode.OK, status_text=StatusCodeDescription[StatusCode.OK])
        except TypeError as e:
            return Response(status=StatusCode.BADREQUEST, status_text=str(e))
        except ValueError as e:
            return Response(status=e.args[0], status_text=e.args[1])
        except Exception as e:
            return Response(status=StatusCode.INTERNALERROR, status_text="File not updated")

    def update_handler(self, **kwargs):
        """This method manages the execution of `update` commands.

        If the system is currently operating in `DB Mode`, it switches the SLPF Actuator Manager to `FILE Mode`,
        removing all rules from the database and all associated scheduled commands from the scheduler.
        Finally, it executes the `update` action in the specific `SLPF Actuator environment`.

        :param kwargs: A dictionary of actuator-specific arguments.
        :type kwargs: dict
        """

        try:
            if self.mode == SLPFActuator.Mode.db:
                #   Setting SLPF Actuator Manager in FILE Mode
                self.mode = SLPFActuator.Mode.file
                logger.info(self.tag + " " + self.mode.value + " mode setted")
                #   Cleaning the scheduler of allow, deny and delete commands
                #   (related to rules that will be deleted)
                for job in self.scheduler.get_jobs():
                    if job.func.__name__ != self.update_handler.__name__:
                        self.scheduler.remove_job(job.id)
                #   Cleaning database (SLPF Actuator Manager now in file mode, all rules managed by file)
                self.db.clean_db()
                #   Cleaning all rules in the specific actuator environment
                self.clean_actuator_rules()
                self.save_persistent_commands()

            #   Executing the update action in the specific actuator environment
            self.execute_update_command(**kwargs)

            logger.info(self.tag + " Update action executed successfully")
        except Exception as e:
            logger.info(self.tag + " Execution error for update action: %s", str(e))
            e.arg = {"command_action": Actions.update}
            raise e

    def slpf_exit(self):
        """This method handles SLPF Actuator Manager `shutdown`.

        It deletes all non-persistent commands from the database,
        saves persistent commands and scheduled jobs if SLPF Actuator in db mode and
        turns off the scheduler.
        """

        try:
            #   Deleting non persistent commands
            logger.info(self.tag + " Deleting non persistent commands")
            non_persistent_commands = self.db.get_non_persistent_comands()
            for command in non_persistent_commands:
                scheduler_data = command["scheduler_data"]
                scheduler_data["my_id"] = None

                self.delete_handler(
                    command_to_delete=self.reconstruct_command(command),
                    rule_number=command["rule_number"],
                    custom_data=None,
                    job_ids=scheduler_data,
                )

            #   Saving persistent commands only if the SLPF Actuator Manager is in DB Mode (there are rules in the database)
            logger.info(self.tag + " " + self.mode.value + " mode")
            if self.mode == SLPFActuator.Mode.db:
                self.save_persistent_commands()

            #   Saving unexecuted scheduler jobs
            logger.info(self.tag + " Saving persistent scheduled jobs")
            persistent_jobs = self.scheduler.get_jobs()
            if persistent_jobs:
                for job in persistent_jobs:
                    self.db.insert_job(
                        id=job.id,
                        func_name=job.func.__name__,
                        next_run_time=job.next_run_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                        args=job.args,
                        kwargs=job.kwargs,
                    )

                    #   Shutting down the scheduler
            threading.Thread(target=self.scheduler.shutdown).start()
            logger.info(self.tag + " Shutdown")
        except Exception as e:
            logger.info(self.tag + " Shutdown error: %s", str(e))
            raise e

    def scheduler_listener(self, event):
        """This method handles success or exceptions of scheduled `APScheduler jobs`.

        :param event: An event triggered by the execution of a job (success or exception).
        :type event: apscheduler.events.JobExecutionEvent
        """

        try:
            if event.exception:
                if hasattr(event.exception, "arg"):
                    command_action = event.exception.arg.get("command_action")
                    if not command_action:
                        raise
                    if command_action == Actions.allow or command_action == Actions.deny:
                        self.db.delete_command(event.exception.arg.get("rule_number"))
                    elif command_action == Actions.delete:
                        pass
                    elif command_action == Actions.update:
                        pass
        except Exception as e:
            raise e

    def restore_persistent_jobs(self):
        """This method restores scheduled `APScheduler jobs` not executed yet."""

        try:
            persistent_jobs = self.db.get_jobs()
            for job in persistent_jobs:
                self.scheduler.add_job(
                    getattr(self, job["func_name"]),
                    "date",
                    next_run_time=datetime.strptime(job["next_run_time"], "%Y-%m-%d %H:%M:%S.%f"),
                    args=job["args"],
                    kwargs=job["kwargs"],
                    id=job["id"],
                    misfire_grace_time=self.misfire_grace_time,
                )
            self.db.delete_jobs()
        except Exception as e:
            raise e

    def generate_unique_job_id(self):
        """This method generates an unique ID for an `APScheduler job` that has to be scheduled.

        :return: The generated `unique id`.
        :rtype: str
        """

        while True:
            job_id = str(uuid.uuid4())
            if not self.scheduler.get_job(job_id):
                return job_id

    def db_handler(self, action, target, args, custom_data, scheduler_data):
        """This method handles insertion of OpenC2 Commands and associated custom data into the database.

        :param action: The command `Action` to be inserted.
        :type action: Actions
        :param target: The command `Target` to be inserted.
        :type target: IPv4Net/IPv6Net/IPv4Connection/IPv6Connection
        :param args: The command `Args` to be inserted.
        :type args: slpf.Args
        :param custom_data: Actuator-specific custom data associated with the rule to be saved.
        :type custom_data: dict
        :param scheduler_data: Contains information about `APScheduler job IDs`:
                                `start_job_id` is the ID of the job responsible to activate, at a certain `start time`, the OpenC2 allow or deny action,
                                `stop_job_id` is the ID of the job responsible to deactivate, at a certain `stop time`, the OpenC2 allow or deny action.
        :type job_ids: dict
        """

        try:
            src = None
            src_port = None
            dst = None
            dst_port = None
            prot = None
            if type(target) == IPv4Connection or type(target) == IPv6Connection:
                if target.src_addr:
                    src = target.src_addr.__str__()
                if target.dst_addr:
                    dst = target.dst_addr.__str__()
                if target.protocol:
                    prot = target.protocol.name
                if target.src_port:
                    src_port = target.src_port
                if target.dst_port:
                    dst_port = target.dst_port
            elif type(target) == IPv4Net or type(target) == IPv6Net:
                dst = target.__str__()

            rule_number = self.db.insert_command(
                insert_rule=args["insert_rule"] if "insert_rule" in args else None,
                action=action.__repr__(),
                drop_process=args["drop_process"].name if "drop_process" in args else None,
                direction=args["direction"].name,
                target=target.__class__.__name__,
                protocol=prot,
                src_addr=src,
                src_port=src_port,
                dst_addr=dst,
                dst_port=dst_port,
                start_time=datetime.fromtimestamp(args["start_time"]).isoformat(sep=" ", timespec="milliseconds"),
                stop_time=(
                    datetime.fromtimestamp(args["stop_time"]).isoformat(sep=" ", timespec="milliseconds")
                    if "stop_time" in args
                    else None
                ),
                persistent=args["persistent"] if "persistent" in args else True,
                custom_data=custom_data,
                scheduler_data=scheduler_data,
            )
        except Exception as e:
            raise e
        return rule_number

    def reconstruct_command(self, cmd_data):
        """This method reconstruct an `OpenC2 Command` from `database data`.

        :param cmd_data: Database record related to a specific OpenC2 Command.
        :type cmd_data: dict

        :return: The reconstructed `OpenC2 Command`.
        :rtype: Command
        """

        if cmd_data["action"] == Actions.allow.name:
            action = Actions.allow
        elif cmd_data["action"] == Actions.deny.name:
            action = Actions.deny

        drop_process = None
        if cmd_data["drop_process"]:
            if cmd_data["drop_process"] == DropProcess.none.name:
                drop_process = DropProcess.none
            elif cmd_data["drop_process"] == DropProcess.reject.name:
                drop_process = DropProcess.reject
            elif cmd_data["drop_process"] == DropProcess.false_ack.name:
                drop_process = DropProcess.false_ack

        if cmd_data["direction"] == slpf.Direction.ingress.name:
            direction = slpf.Direction.ingress
        elif cmd_data["direction"] == slpf.Direction.egress.name:
            direction = slpf.Direction.egress
        elif cmd_data["direction"] == slpf.Direction.both.name:
            direction = slpf.Direction.both

        if cmd_data["target"] == IPv4Net.__name__ or cmd_data["target"] == IPv6Net.__name__:
            addr = cmd_data["dst_addr"]

        if cmd_data["target"] == IPv4Net.__name__:
            target = IPv4Net(ipv4_net=addr)
        elif cmd_data["target"] == IPv6Net.__name__:
            target = IPv6Net(ipv6_net=addr)
        elif cmd_data["target"] == IPv4Connection.__name__:
            target = IPv4Connection(
                protocol=cmd_data["protocol"],
                src_addr=cmd_data["src_addr"],
                src_port=cmd_data["src_port"],
                dst_addr=cmd_data["dst_addr"],
                dst_port=cmd_data["dst_port"],
            )
        elif cmd_data["target"] == IPv6Connection.__name__:
            target = IPv6Connection(
                protocol=cmd_data["protocol"],
                src_addr=cmd_data["src_addr"],
                src_port=cmd_data["src_port"],
                dst_addr=cmd_data["dst_addr"],
                dst_port=cmd_data["dst_port"],
            )

        #   Just needed args
        args = slpf.Args({"direction": direction})
        if drop_process:
            args["drop_process"] = drop_process
        reconstructed_command = Command(action, target, args)

        return reconstructed_command

    def __notimplemented(self, cmd):
        """Default response

        Default response returned in case an `Action` is not implemented.
        The `cmd` argument is only present for uniformity with the other handlers.
        :param cmd: The `Command` that triggered the error.
        :return: A `Response` with the appropriate error code.

        """
        return Response(status=StatusCode.NOTIMPLEMENTED, status_text="Command not implemented")

    def __servererror(self, cmd, e):
        """Internal server error

        Default response in case something goes wrong while processing the command.
        :param cmd: The command that triggered the error.
        :param e: The Exception returned.
        :return: A standard INTERNALSERVERERROR response.
        """
        logger.warn("Returning details of internal exception")
        logger.warn("This is only meant for debugging: change the log level for production environments")
        if logging.root.level < logging.INFO:
            return Response(status=StatusCode.INTERNALERROR, status_text="Internal server error: " + str(e))
        else:
            return Response(status=StatusCode.INTERNALERROR, status_text="Internal server error")

import logging
import os
import threading
import json

from typing_extensions import deprecated

from otupy.actuators.nfm.handlers.argument_handler import get_sleep_times
from otupy.actuators.rcli.utils.random_name_generator import generate_unique_name
import otupy.profiles.nfm as nfm
from otupy.actuators.nfm.utils.bpf_filter_translator import generate_bpf_filter
from otupy.profiles.nfm.targets.monitor_id import MonitorID
from otupy.actuators.nfm.handlers.response_handler import badrequest, ok
from otupy.actuators.nfm.utils.process_utils import run_monitor
from otupy.actuators.nfm.nfm_actuator import NFMActuator
from otupy import Feature, actuator_implementation

# Initialize logger
logger = logging.getLogger(__name__)

IE_MAP="ie/nprobe.json"

@actuator_implementation("nfm-nprobe")
class NFMActuatorNProbe(NFMActuator):
    __features = {
        "exports": ["collector", "file"],
        "export_options": ["sampling", "aggregate", "buffer", "timeout"],
        "flow_format": ["netflow5", "netflow7", "json", "csv"],
        "filters": ["source / destination", "ipv4 / ipv6", "port", "protocol"],
        "info_elements": {},
    }

    def __init__(self, *, specifiers, probe, **kwargs):
        super().__init__(asset_id=specifiers["asset_id"])
        self.probe = probe
        self.allowed_interfaces = probe.get("allowed_interfaces", [])
        self.__features["info_elements"] = self._load_information_elements()

    def _load_information_elements(self):
        iemap_path = os.path.join(os.path.dirname(__file__), IE_MAP)
        try:
            with open(iemap_path, 'r') as f:
                iemap = json.load(f)
                if iemap:
                    return iemap
                else:
                    return {}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load information element mapping: {e}")
            return {}


    def _handle_feature(self, f):
        match f:
            case Feature.information_elements:
                return self.__features["info_elements"].keys()
            case Feature.exports:
                return self.__features["exports"]
            case Feature.export_options:
                return self.__features["export_options"]
            case Feature.flow_format:
                return self.__features["flow_format"]
            case Feature.filters:
                return self.__features["filters"]
            case _:
                return super()._handle_feature(f)

    def _start_monitor(self, cmd):
        monitor = cmd.target.getObj()
        args = cmd.args or {}
        if 'executable' not in self.probe:
            logger.error("No nprobe executable provided, skipping command")
            return servererror("Invalid configuration")
        cmd_list = [self.probe.get('executable', None)]
        cmd_list = self._add_interfaces(cmd_list, monitor)
        cmd_list = self._add_bpf_filter(cmd_list, monitor)
        cmd_list = self._add_information_elements(cmd_list, monitor)
        cmd_list = self._add_exporter_options(cmd_list, args)
        sleep_time, terminate_time = get_sleep_times(args)
        monitor_id = generate_unique_name()
        if sleep_time > 0:
            threading.Timer(sleep_time, run_monitor, args=(cmd_list, terminate_time, monitor_id)).start()
            return ok("Monitor will start after delay", nfm.Results(monitor_id=MonitorID(monitor_id)))
        return run_monitor(cmd_list, terminate_time, monitor_id)

    # Private helper functions
    def _add_interfaces(self, cmd_list, monitor):
        if monitor.get("interfaces"):
            cmd_list += ["--interface"] + [iface.name for iface in monitor.interfaces]
        return cmd_list

    def _add_bpf_filter(self, cmd_list, monitor):
        bpf_filters = (
            generate_bpf_filter(monitor.filter_v4, monitor.filter_v6)
            if monitor.get("filter_v4") or monitor.get("filter_v6")
            else None
        )
        if bpf_filters:
            cmd_list += ["-f", f"'{bpf_filters}'"]
        return cmd_list

    def _add_information_elements(self, cmd_list, monitor):
        if monitor.get("information_elements"):
            cmd_list += ["-T"]
#            value = self.config.get_info_element(self.asset_id, monitor.information_elements)
            values = [self.__features["info_elements"].get(k) for k in monitor.information_elements]
            if None in values:
                return badrequest("Information element is not supported")
            cmd_list.extend(values)
        return cmd_list

    def _add_exporter_options(self, cmd_list, args):
        exporter = args.get("exporter")
        if exporter:
            cmd_list = self._add_exporter_storage(cmd_list, exporter)
            cmd_list = self._add_exporter_collectors(cmd_list, exporter)

        opts = args.get("exporter_options", {})
        cmd_list = self._add_option(cmd_list, opts, "sampling", "--sampling-rate")
        cmd_list = self._add_option(cmd_list, opts, "aggregate", "--aggregate")
        cmd_list = self._add_option(cmd_list, opts, "buffer", "--collector-buffer-size")
        cmd_list = self._add_option(cmd_list, opts, "timeout", "--collector-timeout")
        cmd_list = self._add_option(cmd_list, opts, "format", "-D")

        return cmd_list

    def _add_exporter_storage(self, cmd_list, exporter):
        if exporter.storage:
            path = os.path.join(exporter.storage.get("path", ""), exporter.storage.get("name", ""))
            cmd_list += ["-P", path]
        return cmd_list

    def _add_exporter_collectors(self, cmd_list, exporter):
        for c in exporter.collectors or []:
            if c.host:
                if c.port:
                    cmd_list += ["--collector", f"{c.host.getObj()}:{c.port}"]
        return cmd_list

    def _add_option(self, cmd_list, opts, opt, flag):
        val = opts.get(opt)
        if val:
            cmd_list += [flag, str(val)]
        return cmd_list

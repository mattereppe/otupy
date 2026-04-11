import logging
import threading

import otupy.profiles.nfm as nfm
from otupy.actuators.rcli.utils.random_name_generator import generate_unique_name
from otupy import Feature, actuator_implementation
from otupy.actuators.nfm.handlers.argument_handler import get_sleep_times
from otupy.actuators.nfm.handlers.response_handler import ok
from otupy.actuators.nfm.nfm_actuator import NFMActuator
from otupy.actuators.nfm.utils.bpf_filter_translator import generate_bpf_filter
from otupy.actuators.nfm.utils.process_utils import run_monitor
from otupy.profiles.nfm.targets.monitor_id import MonitorID

logger = logging.getLogger(__name__)


@actuator_implementation("nfm-fprobe")
class NFMActuatorFProbe(NFMActuator):
    __features = {
        "exports": ["collector"],
        "export_options": [
            "buffer",
            "format",
        ],
        "flow_format": ["netflow5", "netflow7"],
        "filters": ["source / destination", "ipv4 / ipv6", "port", "protocol"],
        "info_elements": [],
    }

    def __init__(self, *, specifiers, probe, **kwargs):
        super().__init__(asset_id=specifiers["asset_id"])
        self.probe = probe

    def _handle_feature(self, f):
        match f:
            case Feature.information_elements:
                return self.__features["info_elements"]
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
        cmd_list = [self.probe["executable"], "-l", "2"]
        cmd_list = self._add_interfaces(cmd_list, monitor)
        cmd_list = self._add_bpf_filter(cmd_list, monitor)
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
            cmd_list += ["-i"] + [iface.name for iface in monitor.interfaces]
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

    def _add_exporter_options(self, cmd_list, args):
        exporter = args.get("exporter")

        opts = args.get("exporter_options", {})
        cmd_list = self._add_option(cmd_list, opts, "buffer", "-B")
        cmd_list = self._add_option(cmd_list, opts, "format", "-n")
        if exporter:
            cmd_list = self._add_exporter_collectors(cmd_list, exporter)

        return cmd_list

    def _add_exporter_collectors(self, cmd_list, exporter):
        for c in exporter.collectors or []:
            if c.address:
                if c.port:
                    cmd_list += [f"{c.address()}:{c.port}"]
        return cmd_list

    def _add_option(self, cmd_list, opts, opt, flag):
        val = opts.get(opt)
        if val:
            value = str(val)
            if opt == "format":
                value = value[7:]
            cmd_list += [flag, value]
        return cmd_list

import yaml

from otupy.actuators.nfm.nfm_actuator import NFMActuator
from otupy.actuators.nfm.handlers.response_handler import ok
import threading, logging, os
from otupy.actuators.nfm.handlers.argument_handler import get_sleep_times
from otupy.actuators.nfm.utils.random_name_generator import generate_unique_name
import otupy.profiles.nfm as nfm
from otupy.actuators.nfm.utils.bpf_filter_translator import generate_bpf_filter

from otupy.profiles.nfm.targets.monitor_id import MonitorID
from otupy import Feature, actuator_implementation
from otupy.actuators.nfm.utils.process_utils import run_monitor

logger = logging.getLogger(__name__)

DEFAULT_COLLECTOR_ADDRESS="127.0.0.1"
DEFAULT_COLLECTOR_PORT="2055"

@actuator_implementation("nfm-packetbeat")
class NFMActuatorPacketbeat(NFMActuator):
    __features = {
        "exports": ["file"],
        "export_options": ["sampling"],
        "flow_format": ["json"],
        "filters": ["source / destination", "ipv4 / ipv6", "port", "protocol"],
        "info_elements": [
            "@timestamp",
            "@metadata.beat",
            "@metadata.type",
            "@metadata.version",
            "type",
            "ecs.version",
            "event.start",
            "event.end",
            "event.duration",
            "event.category",
            "event.action",
            "host.name",
            "host.hostname",
            "host.ip",
            "host.mac",
            "host.os",
            "host.id",
            "host.containerized",
            "agent.name",
            "agent.version",
            "agent.id",
            "flow.id",
            "flow.final",
            "network.transport",
            "network.community_id",
            "network.bytes",
            "network.packets",
            "network.type",
            "source.ip",
            "source.port",
            "source.bytes",
            "source.packets",
            "destination.ip",
            "destination.port",
            "destination.bytes",
            "destination.packets",
        ],
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

        interfaces, information_elements, output, bpf_filters, sampling = self._parse_monitor(monitor, args)
        sleep_time, terminate_time = get_sleep_times(args)

        if args.get("exporter"):
            output = self._get_output(args)
            collectors = self._get_collectors(args)
        monitor_id = generate_unique_name()
        config_file_name = self._configure_packetbeat_yaml(
            interfaces, information_elements, bpf_filters, output, collectors, sampling, monitor_id
        )
        cmd_list = [self.probe["executable"], "-c", config_file_name]
        if sleep_time > 0:
            threading.Timer(sleep_time, run_monitor, args=(cmd_list, terminate_time, monitor_id)).start()
            return ok("Monitor will start after delay", nfm.Results(monitor_id=MonitorID(monitor_id)))
        return run_monitor(cmd_list, terminate_time, monitor_id)

    def _parse_monitor(self, monitor, args):
        interfaces = [iface.name for iface in monitor.get("interfaces", [])]
        if self.probe["info_elements"] is not None:
            information_elements = self.probe["info_elements"]
        else:
            information_elements = self.__features["info_elements"]
        bpf_filters = (
            generate_bpf_filter(monitor.filter_v4, monitor.filter_v6)
            if monitor.get("filter_v4") or monitor.get("filter_v6")
            else None
        )
        sampling = args.get("exporter_options", {}).get("sampling")
        return interfaces, information_elements, None, bpf_filters, sampling

    def _get_output(self, args):
        exporter = args.get("exporter")
        if exporter and exporter.get("storage"):
            return exporter.storage.get("path", ""), exporter.storage.get("name", "")
        return None

    def _get_collectors(self, args):
        collectors = []
        exporter = args.get("exporter")
        if exporter and exporter.get("collector"):
            for c in exporter.get("collector"):
                collectors.append( (c.get("address", DEFAULT_COLLECTOR_ADDRESS), c.get("port", DEFAULT_COLLECTOR_PORT)) )
        return collectors

    def _configure_packetbeat_yaml(self, interfaces, information_elements, bpf_filters, output, collectors, sampling, monitor_id):
        try:
            config = self._load_yaml_config(self.probe["base_config"])
            self._update_packetbeat_config(
                config, interfaces, information_elements, bpf_filters, output, collectors, sampling, monitor_id
            )
            return self._write_yaml_config(config, monitor_id)
        except Exception as e:
            logger.error(f"Error configuring packetbeat: {e}")
            raise

    def _load_yaml_config(self, path):
        if path is None:
            return {}
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

    def _update_packetbeat_config(
        self, config, interfaces, information_elements, bpf_filters, output, collectors, sampling, monitor_id
    ):
        config.setdefault("packetbeat", {})
        if monitor_id:
            data_path = os.path.join(self.probe["data_directory"], monitor_id)
            config.setdefault("path", {})["data"] = data_path
        if interfaces:
            config["packetbeat"]["interfaces"] = [{"device": iface, "bpf_filter": bpf_filters} for iface in interfaces]
        if bpf_filters:
            for iface_config in config["packetbeat"]["interfaces"]:
                iface_config["bpf_filter"] = bpf_filters
        if sampling:
            config["packetbeat"]["flows"] = {"period": f"{sampling}s"}
        if output:
            log_path = os.path.join(self.probe["log_directory"], output[0])
            config["output"] = {
                "file": {"path": log_path, "filename": output[1], "rotate_every_kb": 3000, "number_of_files": 5}
            }
        for c in collectors:
            # TODO: We currently support logstash only, since additional outputs (Kafka, Redis, Elasticsearch
            # would require more parameters in the profile (e.g., topic name, index, ...
            hosts = "[" + c[0] + ":" + c[1] + "]"
            config["output"] = {
                "logstash": {"hosts": hosts }
            }
        if information_elements:
            config["processors"] = [{"include_fields": {"fields": information_elements}}]

    def _write_yaml_config(self, config, monitor_id):
        file_name = os.path.join(self.probe["config_directory"], f"packetbeat_{monitor_id}.yml")
        try:
            with open(file_name, "w") as f:
                yaml.safe_dump(config, f)
            logger.info("Packetbeat configuration updated successfully.")
            return file_name
        except Exception as e:
            raise Exception(f"Failed to update Packetbeat configuration: {e}")

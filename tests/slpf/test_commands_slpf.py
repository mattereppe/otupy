import datetime
import ipaddress
import itertools
import logging
import signal
import subprocess
import threading
import time

import pytest

import otupy.profiles.slpf as slpf
import tests.slpf.json_schema_validation_slpf as json_schema_validation_slpf
from otupy import (
    Encoder,
    Command,
    Response,
    Message,
    StatusCode,
    Actions,
    Args,
    ResponseType,
    DateTime,
    Duration,
    IPv4Connection,
    IPv6Connection,
    IPv4Net,
    IPv6Net,
    L4Protocol,
    Port,
    File,
    Hashes,
    Binaryx,
    Features,
    Feature,
)
from otupy.core.producer import Producer
from otupy.encoders.json import JSONEncoder
from otupy.profiles.slpf.args import Direction
from otupy.profiles.slpf.data import DropProcess
from otupy.transfers.http.http_transfer import HTTPTransfer

good_query_commands = []
good_allow_commands = []
bad_allow_commands = []
good_deny_commands = []
bad_deny_commands = []
good_delete_commands = []
good_update_commands = []
bad_update_commands = []


def generate_commands(
    asset_id,
    src_addr_ipv4,
    src_addr_ipv6,
    dst_addr_ipv4,
    dst_addr_ipv6,
    src_port,
    dst_port,
    file_name_v4=None,
    file_path_v4=None,
    file_hash_md5_v4=None,
    file_hash_sha1_v4=None,
    file_hash_sha256_v4=None,
    file_name_v6=None,
    file_path_v6=None,
    file_hash_md5_v6=None,
    file_hash_sha1_v6=None,
    file_hash_sha256_v6=None,
):
    # 	Query
    generate_query_commands(asset_id)
    # 	Allow
    generate_allow_deny_target_commands(
        asset_id,
        Actions.allow,
        src_addr_ipv4,
        src_addr_ipv6,
        dst_addr_ipv4,
        dst_addr_ipv6,
        src_port,
        dst_port,
        good_allow_commands,
        bad_allow_commands,
    )
    generate_allow_deny_argument_commands(
        asset_id,
        Actions.allow,
        src_addr_ipv4,
        dst_addr_ipv4,
        L4Protocol.tcp,
        src_port,
        dst_port,
        good_allow_commands,
        bad_allow_commands,
    )
    # 	Deny
    if asset_id == "iptables":
        generate_allow_deny_target_commands(
            asset_id,
            Actions.deny,
            src_addr_ipv4,
            src_addr_ipv6,
            dst_addr_ipv4,
            dst_addr_ipv6,
            src_port,
            dst_port,
            good_deny_commands,
            bad_deny_commands,
        )
        generate_allow_deny_argument_commands(
            asset_id,
            Actions.deny,
            src_addr_ipv4,
            dst_addr_ipv4,
            L4Protocol.tcp,
            src_port,
            dst_port,
            good_deny_commands,
            bad_deny_commands,
        )
    # 	Delete
    generate_delete_argument_commands(asset_id)
    # 	Update
    if asset_id != "openstack":
        generate_update_target_commands(
            asset_id,
            file_name_v4,
            file_path_v4,
            file_hash_md5_v4,
            file_hash_sha1_v4,
            file_hash_sha256_v4,
            file_name_v6,
            file_path_v6,
            file_hash_md5_v6,
            file_hash_sha1_v6,
            file_hash_sha256_v6,
        )
        generate_update_argument_commands(asset_id, file_name_v4, file_path_v4)


def generate_query_commands(asset_id):
    features = ["versions", "profiles", "pairs", "rate_limit"]
    arg = Args({"response_requested": ResponseType.complete})
    pf = slpf.Specifiers({"asset_id": asset_id})
    for n in range(1, len(features) + 1):
        for combo in itertools.combinations(features, n):
            target = []
            for key in combo:
                if key == "versions":
                    target.append(Feature.versions)
                if key == "profiles":
                    target.append(Feature.profiles)
                if key == "pairs":
                    target.append(Feature.pairs)
            target = Features(target)
            cmd = Command(Actions.query, target, arg, actuator=pf)
            json_cmd = JSONEncoder.todict(cmd)
            good_query_commands.append(json_cmd)


def generate_allow_deny_target_commands(
    asset_id,
    action,
    src_addr_ipv4,
    src_addr_ipv6,
    dst_addr_ipv4,
    dst_addr_ipv6,
    src_port,
    dst_port,
    good_list,
    bad_list,
):
    arguments = ["src_addr", "dst_addr", "protocol", "src_port", "dst_port"]
    arg = slpf.Args({"direction": Direction.both})
    pf = slpf.Specifiers({"asset_id": asset_id})
    for n in range(1, len(arguments) + 1):
        for combo in itertools.combinations(arguments, n):
            ipv4_target = {}
            ipv6_target = {}
            for key in combo:
                if key == "src_addr":
                    ipv4_target["src_addr"] = IPv4Net(src_addr_ipv4)
                    ipv6_target["src_addr"] = IPv6Net(src_addr_ipv6)
                elif key == "dst_addr":
                    ipv4_target["dst_addr"] = IPv4Net(dst_addr_ipv4)
                    ipv6_target["dst_addr"] = IPv6Net(dst_addr_ipv6)
                elif key == "protocol":
                    ipv4_target["protocol"] = L4Protocol.tcp
                    ipv6_target["protocol"] = L4Protocol.tcp
                elif key == "src_port":
                    ipv4_target["src_port"] = Port(src_port)
                    ipv6_target["src_port"] = Port(src_port)
                elif key == "dst_port":
                    ipv4_target["dst_port"] = Port(dst_port)
                    ipv6_target["dst_port"] = Port(dst_port)
            keys = set(ipv4_target.keys())
            ipv4_target = IPv4Connection(**ipv4_target)
            ipv6_target = IPv6Connection(**ipv6_target)
            ipv4_cmd = Command(action, ipv4_target, arg, actuator=pf)
            ipv4_json_cmd = JSONEncoder.todict(ipv4_cmd)
            ipv6_cmd = Command(action, ipv6_target, arg, actuator=pf)
            ipv6_json_cmd = JSONEncoder.todict(ipv6_cmd)

            if "protocol" not in keys and ("src_port" in keys or "dst_port" in keys):
                bad_list.append(ipv4_json_cmd)
                bad_list.append(ipv6_json_cmd)
            else:
                good_list.append(ipv4_json_cmd)
                good_list.append(ipv6_json_cmd)

    types = [IPv4Connection, IPv6Connection]
    # 	types = [IPv4Connection]
    for t in types:
        good_list.append(JSONEncoder.todict(Command(action, t(protocol=L4Protocol.icmp), arg, actuator=pf)))
        good_list.append(JSONEncoder.todict(Command(action, t(protocol=L4Protocol.udp), arg, actuator=pf)))
        good_list.append(JSONEncoder.todict(Command(action, t(protocol=L4Protocol.sctp), arg, actuator=pf)))
        good_list.append(
            JSONEncoder.todict(Command(action, t(protocol=L4Protocol.udp, src_port=src_port), arg, actuator=pf))
        )
        good_list.append(
            JSONEncoder.todict(Command(action, t(protocol=L4Protocol.sctp, src_port=src_port), arg, actuator=pf))
        )
        good_list.append(
            JSONEncoder.todict(Command(action, t(protocol=L4Protocol.udp, dst_port=dst_port), arg, actuator=pf))
        )
        good_list.append(
            JSONEncoder.todict(Command(action, t(protocol=L4Protocol.sctp, dst_port=dst_port), arg, actuator=pf))
        )
        good_list.append(
            JSONEncoder.todict(
                Command(action, t(protocol=L4Protocol.udp, src_port=src_port, dst_port=dst_port), arg, actuator=pf)
            )
        )
        good_list.append(
            JSONEncoder.todict(
                Command(action, t(protocol=L4Protocol.sctp, src_port=src_port, dst_port=dst_port), arg, actuator=pf)
            )
        )

        bad_list.append(
            JSONEncoder.todict(Command(action, t(protocol=L4Protocol.icmp, src_port=src_port), arg, actuator=pf))
        )
        bad_list.append(
            JSONEncoder.todict(Command(action, t(protocol=L4Protocol.icmp, dst_port=dst_port), arg, actuator=pf))
        )
        bad_list.append(
            JSONEncoder.todict(
                Command(action, t(protocol=L4Protocol.icmp, src_port=src_port, dst_port=dst_port), arg, actuator=pf)
            )
        )


def generate_allow_deny_argument_commands(
    asset_id, action, src_addr, dst_addr, protocol, src_port, dst_port, good_list, bad_list
):
    arguments = ["response_requested", "start_time", "stop_time", "duration", "persistent", "insert_rule", "direction"]
    if action == Actions.deny:
        arguments.append("drop_process")
    target = IPv4Connection(
        src_addr=src_addr, dst_addr=dst_addr, protocol=protocol, src_port=src_port, dst_port=dst_port
    )
    pf = slpf.Specifiers({"asset_id": asset_id})
    rule_number = 0
    for n in range(1, len(arguments) + 1):
        for combo in itertools.combinations(arguments, n):
            args = {}
            for key in combo:
                if key == "response_requested":
                    args["response_requested"] = ResponseType.complete
                if key == "start_time":
                    args["start_time"] = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
                if key == "stop_time":
                    args["stop_time"] = int((datetime.datetime.now(datetime.timezone.utc).timestamp() + 2400) * 1000)
                if key == "duration":
                    args["duration"] = Duration(600000)
                if key == "persistent":
                    args["persistent"] = True
                if key == "insert_rule":
                    rule_number += 1000
                    args["insert_rule"] = slpf.RuleID(rule_number)
                if key == "direction":
                    args["direction"] = Direction.both
                if key == "drop_process":
                    args["drop_process"] = DropProcess.none

            keys = set(args.keys())
            if "persistent" in keys or "insert_rule" in keys or "direction" in keys or "drop_process" in keys:
                args = slpf.Args(**args)
            else:
                args = Args(**args)
            cmd = Command(action, target, args, actuator=pf)
            json_cmd = JSONEncoder.todict(cmd)
            if keys == {"persistent"}:
                good_list.append(json_cmd)
                args["persistent"] = False
                cmd = Command(action, target, slpf.Args(**args), actuator=pf)
                json_cmd = JSONEncoder.todict(cmd)
                good_list.append(json_cmd)
                continue
            elif keys == {"direction"}:
                good_list.append(json_cmd)
                args["direction"] = Direction.ingress
                cmd = Command(action, target, slpf.Args(**args), actuator=pf)
                json_cmd = JSONEncoder.todict(cmd)
                good_list.append(json_cmd)
                args["direction"] = Direction.egress
                cmd = Command(action, target, slpf.Args(**args), actuator=pf)
                json_cmd = JSONEncoder.todict(cmd)
                good_list.append(json_cmd)
                continue
            elif keys == {"drop_process"}:
                good_list.append(json_cmd)
                args["drop_process"] = DropProcess.reject
                cmd = Command(action, target, slpf.Args(**args), actuator=pf)
                json_cmd = JSONEncoder.todict(cmd)
                good_list.append(json_cmd)
                args["drop_process"] = DropProcess.false_ack
                cmd = Command(action, target, slpf.Args(**args), actuator=pf)
                json_cmd = JSONEncoder.todict(cmd)
                good_list.append(json_cmd)
                continue

            if "start_time" in keys and "stop_time" in keys and "duration" in keys:
                bad_list.append(json_cmd)
            elif "insert_rule" in keys and "response_requested" not in keys:
                bad_list.append(json_cmd)
            else:
                good_list.append(json_cmd)

    args = {}
    args["start_time"] = int((datetime.datetime.now(datetime.timezone.utc).timestamp() + 90) * 1000)
    args["stop_time"] = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    cmd = Command(action, target, slpf.Args(**args), actuator=pf)
    json_cmd = JSONEncoder.todict(cmd)
    bad_list.append(json_cmd)


def generate_delete_argument_commands(asset_id):
    action = Actions.delete
    rule_number = 1
    response_requested = ResponseType.complete
    start_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    pf = slpf.Specifiers({"asset_id": asset_id})

    args = Args({"response_requested": response_requested})
    json_cmd = JSONEncoder.todict(Command(action, slpf.RuleID(rule_number), args, actuator=pf))
    good_delete_commands.append(json_cmd)

    rule_number += 1
    args = Args({"start_time": start_time})
    json_cmd = JSONEncoder.todict(Command(action, slpf.RuleID(rule_number), args, actuator=pf))
    good_delete_commands.append(json_cmd)

    rule_number += 1
    args = Args({"response_requested": response_requested, "start_time": start_time})
    json_cmd = JSONEncoder.todict(Command(action, slpf.RuleID(rule_number), args, actuator=pf))
    good_delete_commands.append(json_cmd)


def generate_update_target_commands(
    asset_id,
    file_name_v4,
    file_path_v4,
    file_hash_md5_v4,
    file_hash_sha1_v4,
    file_hash_sha256_v4,
    file_name_v6,
    file_path_v6,
    file_hash_md5_v6,
    file_hash_sha1_v6,
    file_hash_sha256_v6,
):
    action = Actions.update
    args = Args({"response_requested": ResponseType.complete})
    pf = slpf.Specifiers({"asset_id": asset_id})

    arguments = ["name", "path", "hashes"]
    for n in range(1, len(arguments) + 1):
        for combo in itertools.combinations(arguments, n):
            target_v4 = {}
            target_v6 = {}
            for key in combo:
                if key == "name":
                    target_v4["name"] = file_name_v4
                    if file_name_v6:
                        target_v6["name"] = file_name_v6
                elif key == "path":
                    target_v4["path"] = file_path_v4
                    if file_path_v6:
                        target_v6["path"] = file_path_v6
                elif key == "hashes":
                    target_v4["hashes"] = Hashes(
                        hashes={
                            "md5": Binaryx(bytes.fromhex(file_hash_md5_v4)),
                            "sha1": Binaryx(bytes.fromhex(file_hash_sha1_v4)),
                            "sha256": Binaryx(bytes.fromhex(file_hash_sha256_v4)),
                        }
                    )
                    if file_hash_md5_v6 or file_hash_sha1_v6 or file_hash_sha256_v6:
                        target_v6["hashes"] = Hashes(
                            hashes={
                                "md5": Binaryx(bytes.fromhex(file_hash_md5_v6)),
                                "sha1": Binaryx(bytes.fromhex(file_hash_sha1_v6)),
                                "sha256": Binaryx(bytes.fromhex(file_hash_sha256_v6)),
                            }
                        )

            keys = set(target_v4.keys())
            target_v4 = File(**target_v4)
            cmd_v4 = Command(action, target_v4, args, actuator=pf)
            json_cmd_v4 = JSONEncoder.todict(cmd_v4)

            if target_v6:
                target_v6 = File(**target_v6)
                cmd_v6 = Command(action, target_v6, args, actuator=pf)
                json_cmd_v6 = JSONEncoder.todict(cmd_v6)

            if keys == {"name", "hashes"}:
                good_update_commands.append(json_cmd_v4)
                target_v4["hashes"] = Hashes(hashes={"md5": Binaryx(bytes.fromhex(file_hash_md5_v4))})
                json_cmd_v4 = JSONEncoder.todict(Command(action, File(**target_v4), args, actuator=pf))
                good_update_commands.append(json_cmd_v4)
                target_v4["hashes"] = Hashes(hashes={"sha1": Binaryx(bytes.fromhex(file_hash_sha1_v4))})
                json_cmd_v4 = JSONEncoder.todict(Command(action, File(**target_v4), args, actuator=pf))
                good_update_commands.append(json_cmd_v4)
                target_v4["hashes"] = Hashes(hashes={"sha256": Binaryx(bytes.fromhex(file_hash_sha256_v4))})
                json_cmd_v4 = JSONEncoder.todict(Command(action, File(**target_v4), args, actuator=pf))
                good_update_commands.append(json_cmd_v4)

                wrong_md5_hash = (
                    file_hash_md5_v4[:-1] + "e" if file_hash_md5_v4.endswith("f") else file_hash_md5_v4[:-1] + "f"
                )
                wrong_sha1_hash = (
                    file_hash_sha1_v4[:-1] + "e" if file_hash_sha1_v4.endswith("f") else file_hash_sha1_v4[:-1] + "f"
                )
                wrong_sha256_hash = (
                    file_hash_sha256_v4[:-1] + "e"
                    if file_hash_sha256_v4.endswith("f")
                    else file_hash_sha256_v4[:-1] + "f"
                )

                target_v4["hashes"] = Hashes(
                    hashes={
                        "md5": Binaryx(bytes.fromhex(wrong_md5_hash)),
                        "sha1": Binaryx(bytes.fromhex(wrong_sha1_hash)),
                        "sha256": Binaryx(bytes.fromhex(wrong_sha256_hash)),
                    }
                )
                json_cmd_v4 = JSONEncoder.todict(Command(action, File(**target_v4), args, actuator=pf))
                bad_update_commands.append(json_cmd_v4)

                target_v4["hashes"] = Hashes(hashes={"md5": Binaryx(bytes.fromhex(wrong_md5_hash))})
                json_cmd_v4 = JSONEncoder.todict(Command(action, File(**target_v4), args, actuator=pf))
                bad_update_commands.append(json_cmd_v4)

                target_v4["hashes"] = Hashes(hashes={"sha1": Binaryx(bytes.fromhex(wrong_sha1_hash))})
                json_cmd_v4 = JSONEncoder.todict(Command(action, File(**target_v4), args, actuator=pf))
                bad_update_commands.append(json_cmd_v4)

                target_v4["hashes"] = Hashes(hashes={"sha256": Binaryx(bytes.fromhex(wrong_sha256_hash))})
                json_cmd_v4 = JSONEncoder.todict(Command(action, File(**target_v4), args, actuator=pf))
                bad_update_commands.append(json_cmd_v4)

                if target_v6:
                    good_update_commands.append(json_cmd_v6)
                    target_v6["hashes"] = Hashes(hashes={"md5": Binaryx(bytes.fromhex(file_hash_md5_v6))})
                    json_cmd_v6 = JSONEncoder.todict(Command(action, File(**target_v6), args, actuator=pf))
                    good_update_commands.append(json_cmd_v6)
                    target_v6["hashes"] = Hashes(hashes={"sha1": Binaryx(bytes.fromhex(file_hash_sha1_v6))})
                    json_cmd_v6 = JSONEncoder.todict(Command(action, File(**target_v6), args, actuator=pf))
                    good_update_commands.append(json_cmd_v6)
                    target_v6["hashes"] = Hashes(hashes={"sha256": Binaryx(bytes.fromhex(file_hash_sha256_v6))})
                    json_cmd_v6 = JSONEncoder.todict(Command(action, File(**target_v6), args, actuator=pf))
                    good_update_commands.append(json_cmd_v6)

                    wrong_md5_hash = (
                        file_hash_md5_v6[:-1] + "e" if file_hash_md5_v6.endswith("f") else file_hash_md5_v6[:-1] + "f"
                    )
                    wrong_sha1_hash = (
                        file_hash_sha1_v6[:-1] + "e"
                        if file_hash_sha1_v6.endswith("f")
                        else file_hash_sha1_v6[:-1] + "f"
                    )
                    wrong_sha256_hash = (
                        file_hash_sha256_v6[:-1] + "e"
                        if file_hash_sha256_v6.endswith("f")
                        else file_hash_sha256_v6[:-1] + "f"
                    )

                    target_v6["hashes"] = Hashes(
                        hashes={
                            "md5": Binaryx(bytes.fromhex(wrong_md5_hash)),
                            "sha1": Binaryx(bytes.fromhex(wrong_sha1_hash)),
                            "sha256": Binaryx(bytes.fromhex(wrong_sha256_hash)),
                        }
                    )
                    json_cmd_v6 = JSONEncoder.todict(Command(action, File(**target_v6), args, actuator=pf))
                    bad_update_commands.append(json_cmd_v6)

                    target_v6["hashes"] = Hashes(hashes={"md5": Binaryx(bytes.fromhex(wrong_md5_hash))})
                    json_cmd_v6 = JSONEncoder.todict(Command(action, File(**target_v6), args, actuator=pf))
                    bad_update_commands.append(json_cmd_v6)

                    target_v6["hashes"] = Hashes(hashes={"sha1": Binaryx(bytes.fromhex(wrong_sha1_hash))})
                    json_cmd_v6 = JSONEncoder.todict(Command(action, File(**target_v6), args, actuator=pf))
                    bad_update_commands.append(json_cmd_v6)

                    target_v6["hashes"] = Hashes(hashes={"sha256": Binaryx(bytes.fromhex(wrong_sha256_hash))})
                    json_cmd_v6 = JSONEncoder.todict(Command(action, File(**target_v6), args, actuator=pf))
                    bad_update_commands.append(json_cmd_v6)

                continue

            if "name" not in keys:
                bad_update_commands.append(json_cmd_v4)
                if target_v6:
                    bad_update_commands.append(json_cmd_v6)
            else:
                good_update_commands.append(json_cmd_v4)
                if target_v6:
                    good_update_commands.append(json_cmd_v6)

    bad_update_commands.append(JSONEncoder.todict(Command(action, File(name=file_name_v4[:-1]), args, actuator=pf)))
    if file_name_v6:
        bad_update_commands.append(JSONEncoder.todict(Command(action, File(name=file_name_v6[:-1]), args, actuator=pf)))
    bad_update_commands.append(JSONEncoder.todict(Command(action, File(name=file_path_v4[:-1]), args, actuator=pf)))
    if file_path_v6:
        bad_update_commands.append(JSONEncoder.todict(Command(action, File(name=file_path_v6[:-1]), args, actuator=pf)))


def generate_update_argument_commands(asset_id, file_name, file_path):
    action = Actions.update
    target = File(name=file_name, path=file_path)
    response_requested = ResponseType.complete
    start_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    pf = slpf.Specifiers({"asset_id": asset_id})

    args = Args({"response_requested": response_requested})
    json_cmd = JSONEncoder.todict(Command(action, target, args, actuator=pf))
    good_update_commands.append(json_cmd)

    args = Args({"start_time": start_time})
    json_cmd = JSONEncoder.todict(Command(action, target, args, actuator=pf))
    good_update_commands.append(json_cmd)

    args = Args({"response_requested": response_requested, "start_time": start_time})
    json_cmd = JSONEncoder.todict(Command(action, target, args, actuator=pf))
    good_update_commands.append(json_cmd)


# 	Iptables
generate_commands(
    asset_id="iptables",
    src_addr_ipv4="10.0.2.6",
    src_addr_ipv6="fe80::a00:27ff:fea2:a157",
    dst_addr_ipv4="10.0.2.15",
    dst_addr_ipv6="fe80::a00:27ff:fe20:2ea9",
    src_port=8080,
    dst_port=8080,
    file_name_v4="new_iptables_rules.v4",
    file_path_v4="/home/kali/Scrivania/openc2lib/examples/slpf/new_iptables_rules.v4",
    file_hash_md5_v4="38511b2bea2d61fb31a63981f4a9fe66",
    file_hash_sha1_v4="51f42a2930a19da436c4ba86363c0fa1eb73d038",
    file_hash_sha256_v4="b804cab981ac13d8b6a12668a589d244caa99dbc6364bf211d8af694be60ddec",
    file_name_v6="new_iptables_rules.v6",
    file_path_v6="/home/kali/Scrivania/openc2lib/examples/slpf/new_iptables_rules.v6",
    file_hash_md5_v6="c3ccc09d9ef7c373de16ca5e904fc687",
    file_hash_sha1_v6="ed75daa4a1bcb67675c66d8035eeccf6cce06c45",
    file_hash_sha256_v6="ad675c0396f490b5c35059bbb9b24c9f12e43c1de339ed04984460777d072b44",
)


# 	OpenStack
# generate_commands(
# 	asset_id='openstack',
# 	src_addr_ipv4='192.168.0.201',
# 	src_addr_ipv6='fe80::f816:3eff:fed8:16b1',
# 	dst_addr_ipv4='192.168.0.202',
# 	dst_addr_ipv6='fe80::f816:3eff:fe5b:130a',
# 	src_port=8080,
# 	dst_port=8080
# )

# 	Kubernetes
# generate_commands(
# 	asset_id='kubernetes',
# 	src_addr_ipv4='10.17.1.25',
# 	src_addr_ipv6='fe80::b459:8ff:fe8d:b6a5',
# 	dst_addr_ipv4='10.17.2.26',
# 	dst_addr_ipv6='fe80::c068:d6ff:fe23:1028',
# 	src_port=8080,
# 	dst_port=8080,
# 	file_name_v4='kubernetes_network_policy.yaml',
# 	file_path_v4='/home/kali/Scrivania/openc2lib/examples/slpf/kubernetes_network_policy.yaml',
# 	file_hash_md5_v4='d42b7f9d90e2fc648ab3b8f15211de08',
# 	file_hash_sha1_v4='bcb775a203e52df46a579f061e4d389aa9871ab7',
# 	file_hash_sha256_v4='cee9a8d1c67df45b165e474bfc0ccbc5c94bab9878bf60a7dd59e38cf8817bb9'
# )


class JSONDump(logging.Filter):
    def filter(self, record):
        return record.getMessage().startswith("HTTP Request Content") or record.getMessage().startswith(
            "HTTP Response Content"
        )


def check_command(cmd):
    assert cmd is not None


@pytest.fixture
def create_producer():
    return Producer("producer.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))


def fix_ip_addresses(cmd):
    """This function fixes ip addresses to compare with json examples provided by third party.
    According to common network practice, an IP network address should always include the prefix/netmask.
    The LS says a Connection should include "IP address range", so this implicitely demands for a prefix
    to be given. However, a single host address may be acceptable as well. Openc2lib strictly adhere to
    the network-biased convention to always give the prefix, but it also accepts ip addresses as input.
    This fix is necessary to convert the reference json examples so that they are comparable with the
    notation of otupy.
    """
    if "ipv4_net" in cmd["target"]:
        cmd["target"]["ipv4_net"] = ipaddress.IPv4Network(cmd["target"]["ipv4_net"]).compressed
    if "ipv6_net" in cmd["target"]:
        cmd["target"]["ipv6_net"] = ipaddress.IPv6Network(cmd["target"]["ipv6_net"]).compressed
    if "ipv4_connection" in cmd["target"]:
        for ip in ["src_addr", "dst_addr"]:
            if ip in cmd["target"]["ipv4_connection"]:
                cmd["target"]["ipv4_connection"][ip] = ipaddress.IPv4Network(
                    cmd["target"]["ipv4_connection"][ip]
                ).compressed
    if "ipv6_connection" in cmd["target"]:
        for ip in ["src_addr", "dst_addr"]:
            if ip in cmd["target"]["ipv6_connection"]:
                cmd["target"]["ipv6_connection"][ip] = ipaddress.IPv6Network(
                    cmd["target"]["ipv6_connection"][ip]
                ).compressed


def fix_hex(cmd):
    """Convert BinaryX values to uppercase, as recommended by the specification"""
    for h in ["md5", "sha1", "sha256"]:
        try:
            if h in cmd["target"]["file"]["hashes"]:
                cmd["target"]["file"]["hashes"][h] = cmd["target"]["file"]["hashes"][h].upper()
        except:
            pass

    if "mac_addr" in cmd["target"]:
        # Use lowercase for similarity to BinaryX
        cmd["target"]["mac_addr"] = cmd["target"]["mac_addr"].upper()


def fix_uuid(cmd):
    """UUID according to RFC 4122 are created as lowercase, but both cases are accepted as input.
    Here we stitch to lowercase for comparison.

    This is a very specific trick for the validation set.
    """
    if "x-acme:container" in cmd["target"]:
        cmd["target"]["x-acme:container"]["container_id"] = cmd["target"]["x-acme:container"]["container_id"].lower()


def validate_json(caplog):
    """Check the openc2 json messages exchanged between the consumer and the producer are valid according to the schema"""

    # WARNING: the visible logs are those generated within this function. Everything else in the fixture does not produce logs
    assert len(caplog.messages) == 2
    msg = caplog.messages[0]
    req = msg[msg.index("\n") + 1 :]
    msg = caplog.messages[1]
    rsp = msg[msg.index("\n") + 1 :]
    print(req)
    print(rsp)
    json_schema_validation_slpf.validate_http(req, json_schema_validation_slpf.Validation.base)
    json_schema_validation_slpf.validate_http(req, json_schema_validation_slpf.Validation.contrib)
    json_schema_validation_slpf.validate_http(rsp, json_schema_validation_slpf.Validation.base)
    json_schema_validation_slpf.validate_http(rsp, json_schema_validation_slpf.Validation.contrib)

    return True


@pytest.mark.parametrize(
    "cmd",
    good_query_commands
    + good_allow_commands
    + good_deny_commands
    + good_delete_commands
    + good_update_commands
    + bad_allow_commands
    + bad_deny_commands
    + bad_update_commands,
)
@pytest.mark.dependency(name="test_decoding")
def test_decoding(cmd):
    """Test 'good' commands can be successfully decoded by otupy"""
    print("Command json: ", cmd)
    c = JSONEncoder.decode(cmd, Command)
    assert type(c) == Command


@pytest.mark.parametrize(
    "cmd",
    good_query_commands
    + good_allow_commands
    + good_deny_commands
    + good_delete_commands
    + good_update_commands
    + bad_allow_commands
    + bad_deny_commands
    + bad_update_commands,
)
def test_encoding(cmd):
    """Test 'good' commands can be successfully encoded by otupy

    The test decodes 'good' commands, and then create again the json. Finally, the original
    and created json are compared. A number of fixes are applied to account for different
    representations of the values (e.g., lowercase/uppercase).
    """
    print("Command json: ", cmd)
    oc2_cmd = JSONEncoder.decode(cmd, Command)
    # Use to dict because the Encoder.encode method returns a str
    oc2_json = JSONEncoder.todict(oc2_cmd)
    print(oc2_json)

    fix_ip_addresses(cmd)
    fix_hex(cmd)
    fix_uuid(cmd)

    assert cmd == oc2_json


@pytest.mark.parametrize("cmd", good_allow_commands)
def test_sending_allow(cmd, create_producer, caplog):
    """Test 'good' messages are successfully sent to the remote party and a response is received.

    Validate the openc2 json messages exchanged. The response is often an error because the majority
    of features are not implemented in the available actuators.
    """
    c = Encoder.decode(Command, cmd)

    # 	Filter the log to get what I need
    logger = logging.getLogger("otupy.transfers.http.http_transfer")
    logger.addFilter(JSONDump())

    check_command(c)
    print("Command: ", c)

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(c)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK or resp.content.get("status") == StatusCode.NOTIMPLEMENTED
    assert validate_json(caplog) == True

    if "insert_rule" in c.args:
        with caplog.at_level(logging.INFO):
            tmp_resp = create_producer.sendcmd(c)

        assert type(tmp_resp) == Message
        assert type(tmp_resp.content) == Response
        assert tmp_resp.content.get("status") == StatusCode.NOTIMPLEMENTED

    # 	time.sleep(2)

    rule_number = resp.content.get("results")["rule_number"]
    arg = Args({"response_requested": ResponseType.complete})
    pf = slpf.Specifiers({"asset_id": c.actuator.getObj()["asset_id"]})
    temp_cmd = Command(Actions.delete, rule_number, arg, pf)
    check_command(temp_cmd)
    print("Delete command: ", temp_cmd)

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(temp_cmd)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK


# 	time.sleep(2)


@pytest.mark.parametrize("cmd", bad_allow_commands)
def test_sending_invalid_allow(cmd, create_producer, caplog):
    try:
        # Decode and attempt to send the command
        c = Encoder.decode(Command, cmd)
        resp = create_producer.sendcmd(c)

        # Check if the status is BADREQUEST
        if resp.content.get("status") == StatusCode.BADREQUEST:
            # The test succeeds if BADREQUEST status is returned
            return

        # If no exception and status is not BADREQUEST, we raise an error to fail the test
        assert False, "Expected an exception or BADREQUEST status, but neither occurred."

    except Exception as exc:
        # The test succeeds if any exception is raised
        pass


@pytest.mark.parametrize("cmd", good_deny_commands)
def test_sending_deny(cmd, create_producer, caplog):
    """Test 'good' messages are successfully sent to the remote party and a response is received.

    Validate the openc2 json messages exchanged. The response is often an error because the majority
    of features are not implemented in the available actuators.
    """
    c = Encoder.decode(Command, cmd)

    # Filter the log to get what I need
    logger = logging.getLogger("otupy.transfers.http.http_transfer")
    logger.addFilter(JSONDump())

    check_command(c)
    print("Command: ", c)

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(c)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK or resp.content.get("status") == StatusCode.NOTIMPLEMENTED
    assert validate_json(caplog) == True

    if "drop_process" in c.args and c.args["drop_process"] == DropProcess.false_ack:
        return

    if "insert_rule" in c.args:
        with caplog.at_level(logging.INFO):
            tmp_resp = create_producer.sendcmd(c)

        assert type(tmp_resp) == Message
        assert type(tmp_resp.content) == Response
        assert tmp_resp.content.get("status") == StatusCode.NOTIMPLEMENTED

    rule_number = resp.content.get("results")["rule_number"]
    arg = Args({"response_requested": ResponseType.complete})
    pf = slpf.Specifiers({"asset_id": c.actuator.getObj()["asset_id"]})
    temp_cmd = Command(Actions.delete, rule_number, arg, pf)
    check_command(temp_cmd)
    print("Delete command: ", temp_cmd)
    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(temp_cmd)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK


@pytest.mark.parametrize("cmd", bad_deny_commands)
def test_sending_invalid_deny(cmd, create_producer, caplog):
    try:
        # Decode and attempt to send the command
        c = Encoder.decode(Command, cmd)
        resp = create_producer.sendcmd(c)

        # Check if the status is BADREQUEST
        if (
            resp.content.get("status") == StatusCode.BADREQUEST
            or resp.content.get("status") == StatusCode.NOTIMPLEMENTED
        ):
            # The test succeeds if BADREQUEST status is returned
            return

        # If no exception and status is not BADREQUEST, we raise an error to fail the test
        assert False, "Expected an exception or BADREQUEST status, but neither occurred."

    except Exception as exc:
        # The test succeeds if any exception is raised
        pass


@pytest.mark.parametrize("cmd", good_delete_commands)
def test_sending_delete(cmd, create_producer, caplog):
    """Test 'good' messages are successfully sent to the remote party and a response is received.

    Validate the openc2 json messages exchanged. The response is often an error because the majority
    of features are not implemented in the available actuators.
    """
    c = Encoder.decode(Command, cmd)

    # Filter the log to get what I need
    logger = logging.getLogger("otupy.transfers.http.http_transfer")
    logger.addFilter(JSONDump())

    check_command(c)
    print("Command: ", c)

    if c.actuator.getObj()["asset_id"] == "iptables":
        dst_addr = "10.0.2.15"
    elif c.actuator.getObj()["asset_id"] == "openstack":
        dst_addr = "192.168.0.202"
    elif c.actuator.getObj()["asset_id"] == "kubernetes":
        dst_addr = "10.17.2.26"
    arg = slpf.Args(
        {
            "response_requested": ResponseType.complete,
            "insert_rule": int(c.target.getObj()),
            "direction": Direction.ingress,
        }
    )
    pf = slpf.Specifiers({"asset_id": c.actuator.getObj()["asset_id"]})
    allow_cmd = Command(Actions.allow, IPv4Connection(dst_addr=dst_addr), arg, actuator=pf)

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(allow_cmd)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK
    assert validate_json(caplog) == True

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(c)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK


@pytest.mark.parametrize("cmd", good_delete_commands)
def test_sending_invalid_delete(cmd, create_producer, caplog):
    """Test 'good' messages are successfully sent to the remote party and a response is received.

    Validate the openc2 json messages exchanged. The response is often an error because the majority
    of features are not implemented in the available actuators.
    """
    c = Encoder.decode(Command, cmd)

    # Filter the log to get what I need
    logger = logging.getLogger("otupy.transfers.http.http_transfer")
    logger.addFilter(JSONDump())

    check_command(c)
    print("Command: ", c)

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(c)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.INTERNALERROR


@pytest.mark.parametrize("cmd", good_update_commands)
def test_sending_update(cmd, create_producer, caplog):
    """Test 'good' messages are successfully sent to the remote party and a response is received.

    Validate the openc2 json messages exchanged. The response is often an error because the majority
    of features are not implemented in the available actuators.
    """
    c = Encoder.decode(Command, cmd)

    # Filter the log to get what I need
    logger = logging.getLogger("otupy.transfers.http.http_transfer")
    logger.addFilter(JSONDump())

    check_command(c)
    print("Command: ", c)

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(c)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK or resp.content.get("status") == StatusCode.NOTIMPLEMENTED
    assert validate_json(caplog) == True

    time.sleep(0.3)

    if c.actuator.getObj()["asset_id"] == "iptables":
        dst_addr = "10.0.2.15"
    elif c.actuator.getObj()["asset_id"] == "kubernetes":
        dst_addr = "10.17.2.26"
    arg = slpf.Args({"response_requested": ResponseType.complete, "direction": Direction.ingress})
    pf = slpf.Specifiers({"asset_id": c.actuator.getObj()["asset_id"]})
    temp_cmd = Command(Actions.allow, IPv4Connection(dst_addr=dst_addr), arg, actuator=pf)
    check_command(temp_cmd)
    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(temp_cmd)
    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK

    rule_number = resp.content.get("results")["rule_number"]
    arg = slpf.Args({"response_requested": ResponseType.complete})
    temp_cmd = Command(Actions.delete, rule_number, arg, pf)
    check_command(temp_cmd)
    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(temp_cmd)
    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK


@pytest.mark.parametrize("cmd", bad_update_commands)
def test_sending_invalid_update(cmd, create_producer, caplog):
    try:
        # Decode and attempt to send the command
        c = Encoder.decode(Command, cmd)
        resp = create_producer.sendcmd(c)

        # Check if the status is BADREQUEST
        if (
            resp.content.get("status") == StatusCode.BADREQUEST
            or resp.content.get("status") == StatusCode.NOTIMPLEMENTED
        ):
            # The test succeeds if BADREQUEST status is returned
            return

        # If no exception and status is not BADREQUEST, we raise an error to fail the test
        assert False, "Expected an exception or BADREQUEST status, but neither occurred."

    except Exception as exc:
        # The test succeeds if any exception is raised
        pass


@pytest.mark.parametrize("cmd", good_query_commands)
def test_sending_query(cmd, create_producer, caplog):
    """Test 'good' messages are successfully sent to the remote party and a response is received.

    Validate the openc2 json messages exchanged. The response is often an error because the majority
    of features are not implemented in the available actuators.
    """
    c = Encoder.decode(Command, cmd)

    # 	Filter the log to get what I need
    logger = logging.getLogger("otupy.transfers.http.http_transfer")
    logger.addFilter(JSONDump())

    check_command(c)
    print("Command: ", c)

    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(c)

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK or resp.content.get("status") == StatusCode.NOTIMPLEMENTED


def test_iptables_ingress_rules(create_producer, caplog):
    set_rules(
        create_producer,
        caplog,
        asset_id="iptables",
        direction=Direction.ingress,
        traffic_src_addr="10.0.2.6",
        traffic_dst_addr="10.0.2.15",
    )


def test_iptables_egress_rules(create_producer, caplog):
    set_rules(
        create_producer,
        caplog,
        asset_id="iptables",
        direction=Direction.egress,
        traffic_src_addr="10.0.2.6",
        traffic_dst_addr="10.0.2.15",
    )


def test_openstack_ingress_rules(create_producer, caplog):
    set_rules(
        create_producer,
        caplog,
        asset_id="openstack",
        direction=Direction.ingress,
        traffic_src_addr="192.168.0.201",
        traffic_dst_addr="192.168.0.202",
    )


def test_openstack_egress_rules(create_producer, caplog):
    set_rules(
        create_producer,
        caplog,
        asset_id="openstack",
        direction=Direction.egress,
        traffic_src_addr="192.168.0.201",
        traffic_dst_addr="192.168.0.202",
    )


def test_kubernetes_ingress_rules(create_producer, caplog):
    set_rules(
        create_producer,
        caplog,
        asset_id="kubernetes",
        direction=Direction.ingress,
        traffic_src_addr="10.17.1.25",
        traffic_dst_addr="10.17.2.26",
    )


def test_kubernetes_egress_rules(create_producer, caplog):
    set_rules(
        create_producer,
        caplog,
        asset_id="kubernetes",
        direction=Direction.egress,
        traffic_src_addr="10.17.1.25",
        traffic_dst_addr="10.17.2.26",
    )


def set_rules(create_producer, caplog, asset_id, direction, traffic_src_addr, traffic_dst_addr):
    pf = slpf.Specifiers({"asset_id": asset_id})
    delta_time = 0

    if asset_id == "iptables":
        analysis_file = "/home/kali/Scrivania/" + asset_id + "_" + direction.name + "_test.pcap"
        cmd = ["tcpdump", "(icmp or tcp or udp)", "-i", "eth0", "-w", analysis_file]
        tcpdump_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
        delta_time += 10
        target = IPv4Net("10.0.2.0/24")
        arg = slpf.Args(
            {
                "response_requested": ResponseType.complete,
                "direction": direction,
                "start_time": DateTime((now + delta_time) * 1000),
            }
        )
        deny_net_cmd = Command(Actions.deny, target, arg, actuator=pf)

        if direction == Direction.egress:
            hping3_thread = threading.Thread(target=generate_udp_traffic, args=(traffic_src_addr,))
            hping3_thread.start()

        with caplog.at_level(logging.INFO):
            deny_net_resp = create_producer.sendcmd(deny_net_cmd)

        assert type(deny_net_resp) == Message
        assert type(deny_net_resp.content) == Response
        assert deny_net_resp.content.get("status") == StatusCode.OK

        delta_time += 10
    else:
        now = datetime.datetime.combine(datetime.datetime.today(), datetime.time(11, 57)).timestamp()

        if asset_id == "kubernetes":
            delta_time += 10
            target = (
                IPv4Connection(dst_addr="10.17.2.26")
                if direction == Direction.ingress
                else IPv4Connection(src_addr="10.17.2.26")
            )
            arg = slpf.Args(
                {
                    "response_requested": ResponseType.complete,
                    "direction": direction,
                    "start_time": DateTime((now + delta_time) * 1000),
                }
            )
            deny_net_cmd = Command(Actions.allow, target, arg, actuator=pf)

            with caplog.at_level(logging.INFO):
                deny_net_resp = create_producer.sendcmd(deny_net_cmd)

            assert type(deny_net_resp) == Message
            assert type(deny_net_resp.content) == Response
            assert deny_net_resp.content.get("status") == StatusCode.OK

            delta_time += 10

    protocols = (
        [L4Protocol.icmp, L4Protocol.tcp, L4Protocol.udp]
        if asset_id != "kubernetes"
        else [L4Protocol.tcp, L4Protocol.udp]
    )
    for protocol in protocols:
        if asset_id == "openstack":
            delta_time += 10

        src_addr = traffic_src_addr if direction == Direction.ingress else traffic_dst_addr
        dst_addr = traffic_dst_addr if direction == Direction.ingress else traffic_src_addr
        target = IPv4Connection(src_addr=src_addr, dst_addr=dst_addr, protocol=protocol)
        arg = slpf.Args(
            {
                "response_requested": ResponseType.complete,
                "direction": direction,
                "start_time": DateTime((now + delta_time) * 1000),
            }
        )
        allow_conn_prot_cmd = Command(Actions.allow, target, arg, actuator=pf)

        with caplog.at_level(logging.INFO):
            allow_conn_prot_resp = create_producer.sendcmd(allow_conn_prot_cmd)

        assert type(allow_conn_prot_resp) == Message
        assert type(allow_conn_prot_resp.content) == Response
        assert allow_conn_prot_resp.content.get("status") == StatusCode.OK

        delta_time += 10
        target = allow_conn_prot_resp.content.get("results")["rule_number"]
        arg = slpf.Args(
            {"response_requested": ResponseType.complete, "start_time": DateTime((now + delta_time) * 1000)}
        )
        delete_conn_prot_cmd = Command(Actions.delete, target, arg, actuator=pf)

        with caplog.at_level(logging.INFO):
            delete_conn_prot_resp = create_producer.sendcmd(delete_conn_prot_cmd)

        assert type(delete_conn_prot_resp) == Message
        assert type(delete_conn_prot_resp.content) == Response
        assert delete_conn_prot_resp.content.get("status") == StatusCode.OK

    if asset_id != "openstack":
        delta_time += 10
        target = deny_net_resp.content.get("results")["rule_number"]
        arg = slpf.Args(
            {"response_requested": ResponseType.complete, "start_time": DateTime((now + delta_time) * 1000)}
        )
        delete_net_cmd = Command(Actions.delete, target, arg, actuator=pf)

        with caplog.at_level(logging.INFO):
            delete_net_resp = create_producer.sendcmd(delete_net_cmd)

        assert type(delete_net_resp) == Message
        assert type(delete_net_resp.content) == Response
        assert delete_net_resp.content.get("status") == StatusCode.OK

        if asset_id == "iptables":
            delta_time += 10
            time.sleep(delta_time + 2)
            tcpdump_proc.send_signal(signal.SIGINT)
            tcpdump_proc.wait()
            if direction == Direction.egress:
                hping3_thread.join()


def generate_udp_traffic(destination_ip):
    try:
        cmd = ["sudo", "hping3", "--udp", "-c", "15", "-p", "44444", destination_ip]
        while True:
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return
            except subprocess.CalledProcessError as e:
                continue
            except Exception as e:
                raise e
    except Exception as e:
        raise e


@pytest.mark.parametrize("cmd", good_allow_commands)
def test_latency(cmd, create_producer, caplog):
    latency_measurement(
        create_producer, caplog, cmd=cmd, abs_path="/home/kali/Scrivania/openstack/all_del_producer_time.txt"
    )


def latency_measurement(create_producer, caplog, cmd, abs_path):
    allow_cmd = Encoder.decode(Command, cmd)
    # 	Filter the log to get what I need
    logger = logging.getLogger("otupy.transfers.http.http_transfer")
    logger.addFilter(JSONDump())

    check_command(allow_cmd)
    print("Command: ", allow_cmd)

    allow_command_timestamp = time.perf_counter()
    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(allow_cmd)
    allow_response_timestamp = time.perf_counter()

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK

    rule_number = resp.content.get("results")["rule_number"]
    arg = Args({"response_requested": ResponseType.complete})
    pf = slpf.Specifiers({"asset_id": allow_cmd.actuator.getObj()["asset_id"]})
    delete_cmd = Command(Actions.delete, rule_number, arg, pf)
    check_command(delete_cmd)
    print("Delete command: ", delete_cmd)

    time.sleep(0.5)  # iptables
    # 	time.sleep(2)	# openstack, kubernetes

    delete_command_timestamp = time.perf_counter()
    with caplog.at_level(logging.INFO):
        resp = create_producer.sendcmd(delete_cmd)
    delete_response_timestamp = time.perf_counter()

    assert type(resp) == Message
    assert type(resp.content) == Response
    assert resp.content.get("status") == StatusCode.OK

    with open(abs_path, "a") as f:
        f.write(
            f"{allow_response_timestamp - allow_command_timestamp} {delete_response_timestamp - delete_command_timestamp}\n"
        )

    time.sleep(0.5)  # iptables


# 	time.sleep(2)	# openstack, kubernetes

#!../.oc2-env/bin/python3
"""
eBPF Profile - Test & Validation Runner (chained lifecycle)
===========================================================
Because `delete` removes the TC filter, the file from the filesystem AND the
DB record, each command must be measured within a self-consistent lifecycle.
The runner therefore executes a full chain per iteration:

    copy -> create -> query_programs -> delete

so that every iteration starts and ends in a clean state and every command is
exercised in its valid state (all expected to return 200).

query_features is independent (no file required) and is measured separately.

A warm-up phase discards cold-start samples. Latency mean/variance/stdev are
computed per command. An optional --baseline measures the raw `tc filter show`
latency to isolate the OpenC2 overhead.

Usage:
    sudo .oc2-env/bin/python3 test_runner.py --runs 30 --warmup 5 --baseline
"""

import argparse
import hashlib
import json
import logging
import statistics
import time
import csv

import otupy as oc2
from otupy.profiles import rcli
from otupy.profiles.ebpf.data.direction_ebpf import Direction
from otupy.profiles.ebpf.data.hook_program import AttachType
from otupy.profiles.ebpf.data.interfaces_ebpf import Interfaces
from otupy.profiles.ebpf.data.source_file import ProgramFile
from otupy.profiles.ebpf.targets.TCHook.eBPF_program import eBPF_program
from otupy.types.base.array_of import ArrayOf
from otupy.types.targets.file import File
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
import otupy.profiles.ebpf as ebpf

logger = logging.getLogger("test_runner")
logger.setLevel(logging.INFO)
_h = logging.StreamHandler()
_h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(_h)

oc2.Feature.extend("clicommands", 5)

CONFIG = {
    "local_source_path": "/home/abba/ebpf/eBPF_scripts-master/tc_fl_kern.o",
    "storage_path": "tmacp/fcd/a",
    "storage_name": "tc_fl_kernel.o",
    "remote_path": "/opt/abba/tmacp/fcd/a",
    "remote_name": "tc_fl_kernel.o",
    "section": "tc_flowlabel_stats",
    "direction": "ingress",
    "attach_type": "tc",
    "interface": "lo",
    "map_name": "fl_stats",
}


def _status(resp):
    try:
        s = resp.status
        return int(s.value) if hasattr(s, "value") else int(s)
    except Exception:
        return None


def build_query_features():
    return oc2.Command(
        oc2.Actions.query,
        oc2.Features([oc2.Feature.versions, oc2.Feature.profiles, oc2.Feature.pairs]),
        actuator=ebpf.Specifiers({}),
    )


def build_query_programs():
    target = eBPF_program(file=None)
    args = ebpf.Args({"maps_required": False})
    return oc2.Command(oc2.Actions.query, target=target, args=args,
                       actuator=ebpf.Specifiers({}))


def build_copy():
    with open(CONFIG["local_source_path"], "rb") as f:
        bcontent = f.read()
    hashes = oc2.Hashes({"md5": oc2.Binaryx(hashlib.md5(bcontent).digest())})
    artifact = oc2.Artifact(mime_type="application/json",
                            payload=oc2.Binary(bcontent), hashes=hashes)
    storage = File({"path": CONFIG["storage_path"], "name": CONFIG["storage_name"]})
    args = rcli.Args({"storage": storage})
    return oc2.Command(oc2.Actions.copy, artifact, args=args,
                       actuator=ebpf.Specifiers({}))


def build_create():
    prog = ProgramFile(FileName=CONFIG["remote_name"],
                       FilePath=CONFIG["remote_path"],
                       Section=CONFIG["section"])
    target = eBPF_program(file=prog)
    maps = ArrayOf(str)()
    maps.append(CONFIG["map_name"])
    args = ebpf.Args({"Direction": Direction(CONFIG["direction"]),
                      "AttachType": AttachType(CONFIG["attach_type"]),
                      "Interfaces": Interfaces(CONFIG["interface"]),
                      "maps": maps})
    return oc2.Command(oc2.Actions.create, target=target, args=args,
                       actuator=ebpf.Specifiers({}))


def build_delete():
    prog = ProgramFile(FileName=CONFIG["remote_name"],
                       FilePath=CONFIG["remote_path"],
                       Section=CONFIG["section"])
    target = eBPF_program(file=prog)
    args = ebpf.Args({"Direction": Direction(CONFIG["direction"]),
                      "AttachType": AttachType(CONFIG["attach_type"]),
                      "Interfaces": Interfaces(CONFIG["interface"])})
    return oc2.Command(oc2.Actions.delete, target=target, args=args,
                       actuator=ebpf.Specifiers({}))


def _stats(name, lat, status, runs, statuses):
    ok = sum(1 for s in statuses if s == 200)
    return {
        "name": name, "runs": runs, "status": status,
        "ok_count": ok, "fail_count": runs - ok,
        "mean_ms": round(statistics.mean(lat), 3),
        "median_ms": round(statistics.median(lat), 3),
        "variance_ms2": round(statistics.variance(lat) if len(lat) > 1 else 0.0, 3),
        "stdev_ms": round(statistics.stdev(lat) if len(lat) > 1 else 0.0, 3),
        "min_ms": round(min(lat), 3), "max_ms": round(max(lat), 3),
        "samples_ms": [round(x, 3) for x in lat],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--out", default="test_results")
    ap.add_argument("--baseline", action="store_true")
    args = ap.parse_args()

    p = oc2.Producer("producer.example.net", JSONEncoder(),
                     HTTPTransfer(args.host, args.port))

    logger.info("Starting validation (runs=%d, warmup=%d) - chained lifecycle",
                args.runs, args.warmup)

    # Per-command accumulators
    acc = {k: {"lat": [], "st": []} for k in
           ["copy", "create", "query_programs", "delete", "query_features"]}

    def timed(builder):
        cmd = builder()
        t0 = time.perf_counter()
        r = p.sendcmd(cmd)
        t1 = time.perf_counter()
        return (t1 - t0) * 1000.0, _status(r)

    total = args.warmup + args.runs
    for i in range(total):
        record = i >= args.warmup

        # independent idempotent command
        lat, st = timed(build_query_features)
        if record: acc["query_features"]["lat"].append(lat); acc["query_features"]["st"].append(st)

        # full chain: copy -> create -> query -> delete
        lat, st = timed(build_copy)
        if record: acc["copy"]["lat"].append(lat); acc["copy"]["st"].append(st)

        lat, st = timed(build_create)
        if record: acc["create"]["lat"].append(lat); acc["create"]["st"].append(st)

        lat, st = timed(build_query_programs)
        if record: acc["query_programs"]["lat"].append(lat); acc["query_programs"]["st"].append(st)

        lat, st = timed(build_delete)
        if record: acc["delete"]["lat"].append(lat); acc["delete"]["st"].append(st)

    order = ["query_features", "copy", "create", "query_programs", "delete"]
    results = []
    for name in order:
        a = acc[name]
        # representative status = most common
        st = max(set(a["st"]), key=a["st"].count) if a["st"] else None
        r = _stats(name, a["lat"], st, args.runs, a["st"])
        results.append(r)
        logger.info("%-16s status=%s ok=%d/%d mean=%.3f median=%.3f stdev=%.3f ms",
                    name, r["status"], r["ok_count"], r["runs"],
                    r["mean_ms"], r["median_ms"], r["stdev_ms"])

    if args.baseline:
        import subprocess
        lat = []
        for i in range(total):
            t0 = time.perf_counter()
            subprocess.run(["tc", "filter", "show", "dev", CONFIG["interface"], "ingress"],
                           capture_output=True, text=True)
            t1 = time.perf_counter()
            if i >= args.warmup:
                lat.append((t1 - t0) * 1000.0)
        results.append(_stats("baseline_tc_show", lat, "n/a", args.runs, []))

    with open(args.out + ".json", "w") as f:
        json.dump(results, f, indent=2)
    with open(args.out + ".csv", "w", newline="") as f:
        cols = ["name", "runs", "status", "ok_count", "fail_count",
                "mean_ms", "median_ms", "variance_ms2", "stdev_ms", "min_ms", "max_ms"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k, "") for k in cols})

    logger.info("Reports written: %s.json / %s.csv", args.out, args.out)
    print("\n=== SUMMARY (warmup discarded, chained lifecycle) ===")
    print(f"{'Command':<16}{'Status':<8}{'OK':<8}{'Mean':<10}{'Median':<10}{'StDev':<10}")
    for r in results:
        ok = f"{r.get('ok_count','-')}/{r['runs']}" if r.get('ok_count') is not None else "-"
        print(f"{r['name']:<16}{str(r['status']):<8}{ok:<8}{r['mean_ms']:<10}{r['median_ms']:<10}{r['stdev_ms']:<10}")


if __name__ == "__main__":
    main()
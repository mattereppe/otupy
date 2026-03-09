#!/usr/bin/env python3
import sys
from otupy.apps.ebpf.obsolete.producer_manager import (
    create_producer,
    load_program,
    query_programs,
    delete_program
)

ASSET_ID = "ebpf-example"


def print_menu():
    print("\n==== eBPF Producer Menu ====")
    print("1) Load eBPF program")
    print("2) Delete eBPF program")
    print("3) Query loaded programs")
    print("4) Exit")
    print("============================")


def prompt(msg, default=None):
    if default is not None:
        return input(f"{msg} [{default}]: ") or default
    return input(f"{msg}: ")


def menu_load(p):
    print("\n--- Load eBPF Program ---")
    prog = prompt("Program path", "./src/otupy/apps/ebpf/allow_all.o")
    iface = prompt("Interface", "wlp7s0")
    direction = prompt("Direction (ingress/egress/both)", "ingress")
    attach_type = prompt("Attach type (tc/xdp)", "tc")

    try:
        load_program(
            p,
            program_path=prog,
            asset_id=ASSET_ID,
            iface=iface,
            direction=direction,
            attach_type=attach_type
        )
        print("\n Program loaded.")
    except Exception as e:
        print(f"\n Error loading program: {e}")


def menu_delete(p):
    print("\n--- Delete eBPF Program ---")
    prog = prompt("Program path", "./src/otupy/apps/ebpf/allow_all.o")
    iface = prompt("Interface", "wlp7s0")
    direction = prompt("Direction (ingress/egress/both)", "ingress")
    attach_type = prompt("Attach type (tc/xdp)", "tc")

    try:
        delete_program(
            p,
            program_path=prog,
            asset_id=ASSET_ID,
            iface=iface,
            direction=direction,
            attach_type=attach_type
        )
        print("\n Program removed.")
    except Exception as e:
        print(f"\n Error removing program: {e}")


def menu_query(p):
    print("\n--- Query Loaded eBPF Programs ---")
    try:
        query_programs(p, asset_id=ASSET_ID)
    except Exception as e:
        print(f"\n Error querying programs: {e}")


def main():
    print("Starting Producer...")
    p = create_producer()

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            menu_load(p)
        elif choice == "2":
            menu_delete(p)
        elif choice == "3":
            menu_query(p)
        elif choice == "4":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice.\n")


if __name__ == "__main__":
    main()

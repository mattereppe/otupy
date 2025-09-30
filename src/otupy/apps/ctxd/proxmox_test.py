# proxmox_test.py
from proxmoxer import ProxmoxAPI

# ===== CONFIGURE YOUR CONNECTION =====
PROXMOX_HOST = "127.0.0.1"   # or your Proxmox server IP/hostname
USERNAME = "root@pam"        # your Proxmox user
PASSWORD = "yourpassword"    # your Proxmox password
VERIFY_SSL = False            # True if using valid SSL certificate

def main():
    # Connect to Proxmox API
    print("Connecting to Proxmox...")
    proxmox = ProxmoxAPI(
        PROXMOX_HOST,
        user=USERNAME,
        password=PASSWORD,
        verify_ssl=VERIFY_SSL
    )
    print("Connected successfully!\n")

    # List all nodes
    print("Listing all nodes:")
    nodes = proxmox.nodes.get()
    for node in nodes:
        print(f"- Node: {node['node']}")

    # List all VMs on each node
    print("\nListing all VMs on each node:")
    for node in nodes:
        node_name = node['node']
        vms = proxmox.nodes(node_name).qemu.get()
        if not vms:
            print(f"- Node {node_name} has no VMs")
            continue
        for vm in vms:
            print(f"Node: {node_name}, VMID: {vm['vmid']}, Name: {vm.get('name','N/A')}, Status: {vm.get('status','N/A')}")

if __name__ == "__main__":
    main()

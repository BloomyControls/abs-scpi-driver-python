#!/usr/bin/env python

"""Shows how to discover any ABSes on the network using UDP multicast."""

from absscpi import ScpiClient
import sys

def mcast_discovery_demo(interface_ip: str):
    """Demonstrates UDP multicast discovery.

    Args:
        interface_ip: The IP address of the local interface used for multicast
            discovery.
    """
    with ScpiClient() as client:
        # NOTE: we are *not* using an open_* function here! The client need not
        # be connected for this.
        abs_list = client.multicast_discovery(interface_ip)

        print(f"Found {len(abs_list)} device(s)")
        for abs in abs_list:
            print(f"{abs.get_serial()} is at {abs.get_ip_address()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} INTERFACE_IP", file=sys.stderr)
        exit(1)

    mcast_discovery_demo(sys.argv[1])

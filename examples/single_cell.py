#!/usr/bin/env python

"""Shows how to control and measure a single cell."""

from absscpi import ScpiClient
from time import sleep
import sys

def single_cell_demo(ip: str):
    """Demonstrates controlling and measuring a single ABS cell.

    Args:
        ip: The IP address of the ABS.
    """
    with ScpiClient() as client:
        client.open_udp(ip)

        # command cell 0 to 1.5 volts with sourcing and sinking current limits
        # of 5A each
        client.set_cell_voltage(0, 1.5)
        client.set_cell_sourcing(0, 5)
        client.set_cell_sinking(0, 5)

        # enable the cell
        client.enable_cell(0, True)

        # give the cell a little time to settle
        sleep(0.05)

        vmeas = client.measure_cell_voltage(0)
        imeas = client.measure_cell_current(0)

        print(f"measured: {vmeas:.4f}V at {imeas:.4f}A")

        # disable the cell
        client.enable_cell(0, False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} IP", file=sys.stderr)
        exit(1)

    single_cell_demo(sys.argv[1])

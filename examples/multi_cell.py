#!/usr/bin/env python

"""Shows how to control and measure multiple cells at a time.

This can often be more efficient, as it sometimes (though not always) requires
fewer SCPI commands.
"""

from absscpi import ScpiClient
from time import sleep
import sys

def multi_cell_demo(ip: str):
    """Demonstrates controlling and measuring multiple ABS cells at once.

    Args:
        ip: The IP address of the ABS.
    """
    with ScpiClient() as client:
        client.open_udp(ip)

        # command all cells to a scale of voltages
        cell_voltages = [((x + 1) / 8) * 5 for x in range(8)]
        print(f"commanding voltages: {cell_voltages}")

        client.set_all_cell_voltages(cell_voltages)

        # set all current limits to +/-5A
        client.set_all_cell_sourcing([5] * 8)
        client.set_all_cell_sinking([5] * 8)

        client.enable_all_cells([True] * 8)

        # give the cells time to settle
        sleep(0.05)

        vmeas = client.measure_all_cell_voltages()
        imeas = client.measure_all_cell_currents()

        print("Cell\tVoltage\tCurrent")
        for i in range(8):
            print(f"{i+1}\t{vmeas[i]:.4f}\t{imeas[i]:.4f}")

        # disable all cells
        client.enable_all_cells([False] * 8)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} IP", file=sys.stderr)
        exit(1)

    multi_cell_demo(sys.argv[1])

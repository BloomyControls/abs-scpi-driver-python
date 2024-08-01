#!/usr/bin/env python

"""Shows how to address different units and all units over RS-485."""

from absscpi import ScpiClient
import sys

def serial_ids_demo(port: str, ids: list[int]):
    """Demonstrates addressing different ABSes on a serial bus.

    Args:
        port: The COM port to use.
        ids: List of serial IDs to talk to.
    """
    with ScpiClient() as client:
        # first, let's send a message to all units by addressing 32
        # (any number greater than 31 will work)
        client.open_serial(port, 32)

        # set cell 1 to 1.5V on every device
        client.set_cell_voltage(0, 1.5)

        # now ask each unit individually what cell 1's voltage is set to
        for dev_id in ids:
            client.set_target_device_id(dev_id)
            vset = client.get_cell_voltage_target(0)
            print(f"{dev_id} says cell 1 is at {vset}V")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} PORT IDs...", file=sys.stderr)
        exit(1)

    port = sys.argv[1]
    ids = [int(arg) for arg in sys.argv[2:]]

    serial_ids_demo(port, ids)

#!/usr/bin/env python

"""Shows how to query basic device info from the ABS."""

from absscpi import ScpiClient
from textwrap import dedent
import sys

def device_info_demo(ip: str):
    """Demonstrates querying device information and serial ID from the ABS.

    Args:
        ip: The IP address of the ABS.
    """
    with ScpiClient() as client:
        client.open_udp(ip)

        idn = client.get_device_info()
        dev_id = client.get_device_id()
        cal_date = client.get_calibration_date()

        info = f"""
        Part number: {idn.get_part_number()}
        Serial number: {idn.get_serial()}
        FW version: {idn.get_version()}
        ID: {dev_id}
        Calibration date: {cal_date}
        """

        print(dedent(info).strip())

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} IP", file=sys.stderr)
        exit(1)

    device_info_demo(sys.argv[1])

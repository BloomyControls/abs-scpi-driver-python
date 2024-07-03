#!/usr/bin/env python

"""Shows how to use an RS-485 connection to read and write the unit's IP
address."""

from absscpi import ScpiClient
import argparse

def query_ip_demo(port: str, dev_id: int):
    """Demonstrates how to query the IP address of an ABS over serial.

    Args:
        port: The COM port to use.
        dev_id: The device's serial ID.
    """
    with ScpiClient() as client:
        # open the serial port
        client.open_serial(port, dev_id)

        # query the IP and netmask
        addr = client.get_ip_address()

        print("IP:", addr.get_ip_address())
        print("Netmask:", addr.get_netmask())

def set_ip_demo(port: str, dev_id: int, ip: str, netmask: str):
    """Demonstrates how to set the IP address of an ABS over serial.

    Args:
        port: The COM port to use.
        dev_id: The device's serial ID.
        ip: The desired IP address.
        netmask: The desired subnet mask.
    """
    with ScpiClient() as client:
        # open the serial port
        client.open_serial(port, dev_id)

        # set the IP and netmask
        client.set_ip_address(ip, netmask)

if __name__ == "__main__":
    # since this one has a bit more complexity to it, we'll use argparse to
    # handle arguments for us
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', required=True, help='COM port to use')
    parser.add_argument(
            '-i', '--id', required=True, type=int, help="ABS's serial ID")

    subparsers = parser.add_subparsers(dest='command')
    parser_query = subparsers.add_parser(
            'get', help="query the ABS's IP address")

    parser_set = subparsers.add_parser('set', help="set the ABS's IP address")
    parser_set.add_argument('ip', help='IPv4 address, e.g., 192.168.1.70')
    parser_set.add_argument(
            'netmask', nargs='?', default='255.255.255.0',
            help='optional subnet mask, e.g., 255.255.255.0')

    args = parser.parse_args()

    if args.command == 'get':
        query_ip_demo(args.port, args.id)
    elif args.command == 'set':
        set_ip_demo(args.port, args.id, args.ip, args.netmask)

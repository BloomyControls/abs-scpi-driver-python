ABS SCPI Python Library (absscpi)
=================================

Python library for SCPI control of the Bloomy Controls ABS.

Features
--------

- TCP, UDP, RS-485, and UDP multicast
- Supports Windows and Linux
- Implements all SCPI commands and queries supported by the ABS
- Automatic device discovery over UDP multicast and RS-485
- Implemented as a wrapper around `the C/C++ library`_ for a consistent
  interface regardless of the language

.. _the C/C++ library: https://github.com/BloomyControls/abs-scpi-driver

Installation
------------

See `docs/installation.rst <docs/installation.rst>`__ for installation
instructions.

Example usage
-------------

.. code:: python

   from absscpi import ScpiClient
   from time import sleep

   with ScpiClient() as client:
       # open a UDP socket
       client.open_udp("192.168.1.100")

       # get general device information
       id = client.get_device_id()
       ident = client.get_device_info()
       print(f"Device ID: {id}")
       print(f"Part numer: {ident.get_part_number()}")
       print(f"Serial number: {ident.get_serial()}")
       print(f"FW version: {ident.get_version()}")

       # command cell 1 to 1.4V
       client.set_cell_voltage(0, 1.4)
       client.set_cell_sourcing(0, 5.0)
       client.set_cell_sinking(0, 5.0)
       client.enable_cell(0, True)

       sleep(0.05)

       # measure cell 1's voltage
       v = client.measure_cell_voltage(0)
       print(f"Cell 1 voltage: {v}")

       client.enable_cell(0, False)

Discussion
----------

If you find any bugs, you can report them on the GitHub `issue tracker`_.

.. _issue tracker:
   https://github.com/BloomyControls/abs-scpi-driver-python/issues

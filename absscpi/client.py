# Copyright (c) 2024, Bloomy Controls, Inc. All rights reserved.
#
# Use of this source code is governed by a BSD-3-clause license that can be
# found in the LICENSE file or at https://opensource.org/license/BSD-3-Clause

from ctypes import *
from ctypes.util import find_library
from enum import IntEnum, IntFlag
import os
import platform

LIB_NAME = "absscpi"

CELL_COUNT = 8
ANALOG_OUTPUT_COUNT = 8
ANALOG_INPUT_COUNT = 8
DIGITAL_OUTPUT_COUNT = 4
DIGITAL_INPUT_COUNT = 4
GLOBAL_MODEL_INPUT_COUNT = 8
LOCAL_MODEL_INPUT_COUNT = 8
MODEL_OUTPUT_COUNT = 18

class AbsCellFault(IntEnum):
    """ABS cell faulting mode."""
    NONE = 0
    OPEN_CIRCUIT = 1
    SHORT_CIRCUIT = 2
    POLARITY = 3

class AbsCellSenseRange(IntEnum):
    """ABS cell current sense range."""
    AUTO = 0
    LOW_1A = 1
    HIGH_5A = 2

class AbsCellMode(IntEnum):
    """ABS cell operating mode."""
    CV = 0
    ILIM = 1

class AbsDeviceInfo(Structure):
    """Basic information about an ABS."""

    _fields_ = [("part_number", c_char * 128),
                ("serial", c_char * 128),
                ("version", c_char * 128)]

    def get_part_number(self) -> str:
        """Get the device part number."""
        return self.part_number.decode()

    def get_serial(self) -> str:
        """Get the device serial number."""
        return self.serial.decode()

    def get_version(self) -> str:
        """Get the device software version."""
        return self.version.decode()

class AbsEthernetConfig(Structure):
    """ABS Ethernet address configuration."""

    _fields_ = [("ip", c_char * 32),
                ("netmask", c_char * 32)]

    def get_ip_address(self) -> str:
        """Get the IP address."""
        return self.ip.decode()

    def get_netmask(self) -> str:
        """Get the subnet mask."""
        return self.netmask.decode()

class AbsModelStatus(IntFlag):
    """Bits used to decode the ABS model status."""
    RUNNING = 0x01
    LOADED = 0x02
    ERRORED = 0x04

class AbsModelInfo(Structure):
    """Information about a model."""

    _fields_ = [("name", c_char * 256),
                ("version", c_char * 256)]

    def get_name(self) -> str:
        """Get the model's name."""
        return self.name.decode()

    def get_version(self) -> str:
        """Get the model's version."""
        return self.version.decode()

class AbsModelOutputPair(Structure):
    """ABS model output pair."""

    _fields_ = [("value_0", c_float),
                ("value_1", c_float)]

    def to_tuple(self) -> tuple[float, float]:
        """Get the values as a tuple."""
        return (self.value_0.value, self.value_1.value)

class AbsEthernetDiscoveryResult(Structure):
    """ABS Ethernet discovery result."""

    _fields_ = [("ip", c_char * 32),
                ("serial", c_char * 128)]

    def get_ip_address(self) -> str:
        """Get the device's IP address."""
        return self.ip.decode()

    def get_serial(self) -> str:
        """Get the device's serial number."""
        return self.serial.decode()

class AbsSerialDiscoveryResult(Structure):
    """ABS serial discovery result."""

    _fields_ = [("id", c_uint8),
                ("serial", c_char * 128)]

    def get_id(self) -> int:
        """Get the device's serial ID."""
        return self.id.value

    def get_serial(self) -> str:
        """Get the device's serial number."""
        return self.serial.decode()

class ScpiClientError(Exception):
    """SCPI client returned an error."""
    pass

class ScpiClient:
    """Client for communicating with the ABS with SCPI.

    This class supports UDP, TCP, RS-485, and UDP multicast. When using serial
    or multicast, it can broadcast messages to all units on the bus.

    Typical usage example:

    .. code-block:: python

       with ScpiClient() as client:
           client.open_udp("192.168.1.70")
           client.set_cell_voltage(0, 2.3)
           client.enable_cell(0, True)
           # give the cell time to settle
           time.sleep(0.005)
           print(f"Cell 1 measured voltage: {client.measure_cell_voltage(0)}")

    To re-open the connection with the same or a different communication layer,
    you can simply call the corresponding ``open_*()`` method at any time.
    """

    def __init__(self, lib: str = LIB_NAME):
        """
        Args:
            lib: Name of or path to the ABS SCPI DLL. This parameter is
                optional. If the DLL is in a discoverable location such as
                :file:`C:/Windows/System32` or :file:`/usr/lib`, or if it was
                installed to the default path by the Windows MSI installer, it
                will be found automatically. If it is not automatically found,
                pass the path to the file to this function.

        Raises:
            OSError: An error occurred while finding or loading the low-level
                library.
        """
        self.__handle = c_void_p()

        if platform.system() == "Windows":
            load_library_func = windll.LoadLibrary
        else:
            load_library_func = cdll.LoadLibrary

        if platform.system() == "Windows" and lib is LIB_NAME:
            # add the Windows install directory to the lookup path
            os.environ['PATH'] += f";{os.environ['ProgramFiles']}/Bloomy Controls/absscpi/bin"

        lib_path = find_library(lib)
        if not lib_path:
            raise OSError(f"{lib} library not found")

        try:
            self.__dll = load_library_func(lib_path)
        except OSError:
            raise OSError(
                    f"The SCPI library could not be loaded ({lib_path})"
                    ) from None

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def __err_msg(self, err: int) -> str:
        """Get a string describing an error code.

        Args:
            err: The error code.

        Returns:
            A message describing the error code.
        """
        self.__dll.AbsScpiClient_ErrorMessage.restype = c_char_p
        ret = self.__dll.AbsScpiClient_ErrorMessage(err)
        return ret.decode()

    def __check_err(self, err: int):
        """Check a return value and throw an exception if it's an error.

        Args:
            err: The error code returned by a driver function.

        Raises:
            ScpiClientError: The error code is not successful.
        """
        if err < 0:
            raise ScpiClientError(self.__err_msg(err))

    def init(self):
        """Initialize the client handle.

        .. warning::
           Should not be called directly! Use a "with" block instead:

           .. code-block:: python

              with ScpiClient() as client:
                  ...

        Raises:
            ScpiClientError: An error occurred during initialization.
        """
        res = self.__dll.AbsScpiClient_Init(byref(self.__handle))
        self.__check_err(res)

    def cleanup(self):
        """Cleanup the client handle.

        .. warning::
           Should not be called directly! Use a "with" block instead:

           .. code-block:: python

              with ScpiClient() as client:
                  ...
        """
        self.__dll.AbsScpiClient_Destroy(byref(self.__handle))

    def open_udp(self, target_ip: str, interface_ip: str | None = None):
        """Open a UDP connection to the ABS.

        Args:
            target_ip: Target device IP address.
            interface_ip: If present, determines the IP address of the local
                interface to bind the socket to. When not provided, any local
                address may be bound.

        Raises:
            ScpiClientError: An error occurred while opening the socket.
        """
        res = self.__dll.AbsScpiClient_OpenUdp(
                self.__handle, target_ip.encode(),
                interface_ip.encode() if interface_ip else None)
        self.__check_err(res)

    def open_tcp(self, target_ip: str):
        """Open a TCP connection to the ABS.

        Args:
            target_ip: Target device IP address.

        Raises:
            ScpiClientError: An error occurred while attempting to connect.
        """
        res = self.__dll.AbsScpiClient_OpenTcp(
                self.__handle, target_ip.encode())
        self.__check_err(res)

    def open_serial(self, port: str, device_id: int):
        """Open a serial connection to the device.

        Args:
            port: Serial port, such as "COM1" or "/dev/ttyS1."
            device_id: Device's serial ID, 0-31, or 32+ to address all units
                on the bus.

        Raises:
            ScpiClientError: An error occurred while opening the port.
        """
        if device_id < 0:
            raise ValueError(f"device ID out of range: {device_id}")
        res = self.__dll.AbsScpiClient_OpenSerial(
                self.__handle, port.encode(), c_uint(device_id))
        self.__check_err(res)

    def open_udp_multicast(self, interface_ip: str):
        """Open a UDP multicast socket for broadcasting to many ABSes.

        Args:
            interface_ip: IP address of the local NIC to bind to.

        Raises:
            ScpiClientError: An error occurred while opening the socket.
        """
        res = self.__dll.AbsScpiClient_OpenUdpMulticast(
                self.__handle, interface_ip.encode())
        self.__check_err(res)

    def set_target_device_id(self, device_id: int):
        """Set the target device ID for communications.

        Only applies to RS-485 connections.

        Args:
            device_id: Target device ID, 0-31, or 32+ to broadcast to all
                units on the bus.

        Raises:
            ScpiClientError: An error occurred while setting the ID.
        """
        if device_id < 0:
            raise ValueError(f"device ID out of range: {device_id}")
        res = self.__dll.AbsScpiClient_SetTargetDeviceId(
                self.__handle, c_uint(device_id))
        self.__check_err(res)

    def get_target_device_id(self) -> int:
        """Get the target device ID for communications.

        Only relevant for RS-485 connections.

        Returns:
            The target device's ID.

        Raises:
            ScpiClientError: An error occurred while getting the ID.
        """
        dev_id = c_uint()
        res = self.__dll.AbsScpiClient_GetTargetDeviceId(
                self.__handle, byref(dev_id))
        self.__check_err(res)
        return dev_id.value

    def get_device_info(self) -> AbsDeviceInfo:
        """Query basic device information from the device.

        Returns:
            The device information.

        Raises:
            ScpiClientError: An error occurred while opening the port.
        """
        info = AbsDeviceInfo()
        res = self.__dll.AbsScpiClient_GetDeviceInfo(
                self.__handle, byref(info))
        self.__check_err(res)
        return info

    def get_device_id(self) -> int:
        """Query the device's serial ID.

        Returns:
            The device's ID.

        Raises:
            ScpiClientError: An error occurred querying the device.
        """
        dev_id = c_uint8()
        res = self.__dll.AbsScpiClient_GetDeviceId(
                self.__handle, byref(dev_id))
        self.__check_err(res)
        return dev_id.value

    def get_ip_address(self) -> AbsEthernetConfig:
        """Query the device's IP address and subnet mask.

        Returns:
            The Ethernet configuration of the device.

        Raises:
            ScpiClientError: An error occurred querying the device.
        """
        conf = AbsEthernetConfig()
        res = self.__dll.AbsScpiClient_GetIPAddress(
                self.__handle, byref(conf))
        self.__check_err(res)
        return conf

    def set_ip_address(self, ip: str, netmask: str):
        """Set the device's IP address and subnet mask.

        For TCP and UDP connections, you must close and reopen the connection.
        This can be achieved by simply calling the corresponding open_*()
        method again.

        Args:
            ip: Desired IPv4 address.
            netmask: Desired IPv4 subnet mask.

        Raises:
            ScpiClientError: An error occurred sending the command.
        """
        conf = AbsEthernetConfig()
        conf.ip = ip.encode()
        conf.netmask = netmask.encode()
        res = self.__dll.AbsScpiClient_SetIPAddress(
                self.__handle, byref(conf))
        self.__check_err(res)
        return conf

    def get_calibration_date(self) -> str:
        """Query the device's calibration date.

        Returns:
            Device's calibration date.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        buf = create_string_buffer(128)
        res = self.__dll.AbsScpiClient_GetCalibrationDate(
                self.__handle, byref(buf), c_uint(len(buf)))
        self.__check_err(res)
        return buf.value.decode()

    def get_error_count(self) -> int:
        """Query the number of errors in the device's error queue.

        Returns:
            Number of errors in the error queue.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        count = c_int()
        res = self.__dll.AbsScpiClient_GetErrorCount(
                self.__handle, byref(count))
        self.__check_err(res)
        return count.value

    def get_next_error(self) -> tuple[int, str] | None:
        """Query the next error from the device's error queue.

        Returns:
            A tuple containing the returned error code and message or None if
            the error code was 0 (no error).

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        buf = create_string_buffer(256)
        code = c_int16()
        res = self.__dll.AbsScpiClient_GetNextError(
                self.__handle, byref(code), byref(buf), c_uint(len(buf)))
        self.__check_err(res)
        if code.value == 0:
            return None
        return (code.value, buf.value.decode())

    def clear_errors(self):
        """Clear the device's error queue.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_ClearErrors(self.__handle)
        self.__check_err(res)

    def get_alarms(self) -> int:
        """Query the alarms raised on the device.

        Returns:
            The alarms bitmask.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        alarms = c_uint32()
        res = self.__dll.AbsScpiClient_GetAlarms(self.__handle, byref(alarms))
        self.__check_err(res)
        return alarms.value

    def assert_soft_interlock(self):
        """Assert the software interlock (a recoverable alarm).

        The interlock may be cleared using the clear_recoverable_alarms()
        method.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_AssertSoftwareInterlock(self.__handle)
        self.__check_err(res)

    def clear_recoverable_alarms(self):
        """Clear any recoverable alarms raised on the unit (including software
        interlock).

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_ClearRecoverableAlarms(self.__handle)
        self.__check_err(res)

    def reboot(self):
        """Reboot the device, resetting it to its POR state.

        Rebooting takes about 8-10 seconds. If using TCP, you'll need to re-open
        the connection after the device has rebooted.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        self.__check_err(self.__dll.AbsScpiClient_Reboot(self.__handle))

    def enable_cell(self, cell: int, en: bool):
        """Enable or disable a single cell.

        Args:
            cell: Target cell index, 0-7.
            en: Whether to enable the cell.

        Raises:
            ScpiClientError: An error occurred while enabling the cell.
        """
        res = self.__dll.AbsScpiClient_EnableCell(
                self.__handle, c_uint(cell), c_bool(en))
        self.__check_err(res)

    def enable_all_cells(self, en: list[bool]):
        """Enable or disable many cells.

        Args:
            en: List of cell enable states. Must not be longer than the total
                cell count.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        if len(en) > CELL_COUNT:
            raise ValueError("too many inputs")
        elif len(en) == 0:
            return

        cells_on = 0
        cells_off = 0
        for i in range(len(en)):
            if en[i]:
                cells_on |= 1 << i
            else:
                cells_off |= 1 << i

        if cells_on != 0:
            res = self.__dll.AbsScpiClient_EnableCellsMasked(
                    self.__handle, c_uint(cells_on), True)
            self.__check_err(res)

        if cells_off != 0:
            res = self.__dll.AbsScpiClient_EnableCellsMasked(
                    self.__handle, c_uint(cells_off), False)
            self.__check_err(res)

    def get_cell_enabled(self, cell: int) -> bool:
        """Query the enable state of a single cell.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            Whether the cell is enabled.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        en = c_bool()
        res = self.__dll.AbsScpiClient_GetCellEnabled(
                self.__handle, c_uint(cell), byref(en))
        self.__check_err(res)
        return en.value

    def get_all_cells_enabled(self) -> list[bool]:
        """Query the enable state of all cells.

        Returns:
            List of cell enable states, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        states = c_uint()
        res = self.__dll.AbsScpiClient_GetCellsEnabledMasked(
                self.__handle, byref(states))
        self.__check_err(res)
        state_list = [False] * CELL_COUNT
        for i in range(CELL_COUNT):
            if (states.value & (1 << i)) != 0:
                state_list[i] = True
        return state_list

    def set_cell_voltage(self, cell: int, voltage: float):
        """Set a single cell's target voltage.

        Args:
            cell: Target cell index, 0-7.
            voltage: Cell voltage.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_SetCellVoltage(
                self.__handle, c_uint(cell), c_float(voltage))
        self.__check_err(res)

    def set_all_cell_voltages(self, voltages: list[float]):
        """Set all cells' voltages.

        Args:
            voltages: Array of cell voltages. Must not be empty or longer than
                the total cell count.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        vals = (c_float * len(voltages))(*voltages)
        res = self.__dll.AbsScpiClient_SetAllCellVoltages(
                self.__handle, byref(vals), c_uint(len(voltages)))
        self.__check_err(res)

    def get_cell_voltage_target(self, cell: int) -> float:
        """Query a single cell's target voltage.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            The cell's target voltage.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltage = c_float()
        res = self.__dll.AbsScpiClient_GetCellVoltageTarget(
                self.__handle, c_uint(cell), byref(voltage))
        self.__check_err(res)
        return voltage.value

    def get_all_cell_voltage_targets(self) -> list[float]:
        """Query all cells' target voltages.

        Returns:
            An array of voltages, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltages = (c_float * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllCellVoltageTargets(
                self.__handle, byref(voltages), c_uint(CELL_COUNT))
        self.__check_err(res)
        return voltages[:]

    def set_cell_sourcing(self, cell: int, limit: float):
        """Set a single cell's current sourcing limit.

        Args:
            cell: Target cell index, 0-7.
            limit: Sourcing limit.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_SetCellSourcing(
                self.__handle, c_uint(cell), c_float(limit))
        self.__check_err(res)

    def set_all_cell_sourcing(self, limits: list[float]):
        """Set all cells' current sourcing limits.

        Args:
            limits: Array of current limits. Must not be empty or longer than
                the total cell count.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        vals = (c_float * len(limits))(*limits)
        res = self.__dll.AbsScpiClient_SetAllCellSourcing(
                self.__handle, byref(vals), c_uint(len(limits)))
        self.__check_err(res)

    def get_cell_sourcing_limit(self, cell: int) -> float:
        """Query a single cell's current sourcing limit.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            The cell's current sourcing limit.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        limit = c_float()
        res = self.__dll.AbsScpiClient_GetCellSourcingLimit(
                self.__handle, c_uint(cell), byref(limit))
        self.__check_err(res)
        return limit.value

    def get_all_cell_sourcing_limits(self) -> list[float]:
        """Query all cells' current sourcing limits.

        Returns:
            An array of current sourcing limits, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        limits = (c_float * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllCellSourcingLimits(
                self.__handle, byref(limits), c_uint(CELL_COUNT))
        self.__check_err(res)
        return limits[:]

    def set_cell_sinking(self, cell: int, limit: float):
        """Set a single cell's current sinking limit.

        Args:
            cell: Target cell index, 0-7.
            limit: Sinking limit.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_SetCellSinking(
                self.__handle, c_uint(cell), c_float(limit))
        self.__check_err(res)

    def set_all_cell_sinking(self, limits: list[float]):
        """Set all cells' current sinking limits.

        Args:
            limits: Array of current limits. Must not be empty or longer than
                the total cell count.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        vals = (c_float * len(limits))(*limits)
        res = self.__dll.AbsScpiClient_SetAllCellSinking(
                self.__handle, byref(vals), c_uint(len(limits)))
        self.__check_err(res)

    def get_cell_sinking_limit(self, cell: int) -> float:
        """Query a single cell's current sinking limit.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            The cell's current sinking limit.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        limit = c_float()
        res = self.__dll.AbsScpiClient_GetCellSinkingLimit(
                self.__handle, c_uint(cell), byref(limit))
        self.__check_err(res)
        return limit.value

    def get_all_cell_sinking_limits(self) -> list[float]:
        """Query all cells' current sinking limits.

        Returns:
            An array of current sinking limits, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        limits = (c_float * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllCellSinkingLimits(
                self.__handle, byref(limits), c_uint(CELL_COUNT))
        self.__check_err(res)
        return limits[:]

    def set_cell_fault(self, cell: int, fault: AbsCellFault):
        """Set a single cell's faulting state.

        Args:
            cell: Target cell index, 0-7.
            fault: Fault state.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_SetCellFault(
                self.__handle, c_uint(cell), c_int(fault.value))
        self.__check_err(res)

    def set_all_cell_faults(self, faults: list[AbsCellFault]):
        """Set all cells' faulting states.

        Args:
            faults: Array of fault states. Must not be empty or longer than the
                total cell count.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        vals = (c_int * len(faults))(*faults)
        res = self.__dll.AbsScpiClient_SetAllCellFaults(
                self.__handle, byref(vals), c_uint(len(faults)))
        self.__check_err(res)

    def get_cell_fault(self, cell: int) -> AbsCellFault:
        """Query a single cell's faulting state.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            The cell's faulting state.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        state = c_int()
        res = self.__dll.AbsScpiClient_GetCellFault(
                self.__handle, c_uint(cell), byref(state))
        self.__check_err(res)
        return AbsCellFault(state.value)

    def get_all_cell_faults(self) -> list[AbsCellFault]:
        """Query all cells' faulting states.

        Returns:
            An array of faulting states, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        states = (c_int * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllCellFaults(
                self.__handle, byref(states), c_uint(CELL_COUNT))
        self.__check_err(res)
        return [AbsCellFault(state) for state in states]

    def set_cell_sense_range(self, cell: int, range_: AbsCellSenseRange):
        """Set a single cell's current sense range.

        For most applications, changing this setting manually is unnecessary.
        By default, the cell will choose the appropriate sense range based on
        its sourcing and sinking current limits.

        Args:
            cell: Target cell index, 0-7.
            range_: Sense range.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_SetCellSenseRange(
                self.__handle, c_uint(cell), c_int(range_.value))
        self.__check_err(res)

    def set_all_cell_sense_ranges(self, ranges: list[AbsCellSenseRange]):
        """Set all cells' current sense ranges.

        For most applications, changing this setting manually is unnecessary.
        By default, the cells will choose the appropriate sense range based on
        their sourcing and sinking current limits.

        Args:
            ranges: Array of sense ranges. Must not be empty or longer than the
                total cell count.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        vals = (c_int * len(ranges))(*ranges)
        res = self.__dll.AbsScpiClient_SetAllCellSenseRanges(
                self.__handle, byref(vals), c_uint(len(ranges)))
        self.__check_err(res)

    def get_cell_sense_range(self, cell: int) -> AbsCellSenseRange:
        """Query a single cell's current sense range.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            The cell's current sense range.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        range_ = c_int()
        res = self.__dll.AbsScpiClient_GetCellSenseRange(
                self.__handle, c_uint(cell), byref(range_))
        self.__check_err(res)
        return AbsCellSenseRange(range_.value)

    def get_all_cell_sense_ranges(self) -> list[AbsCellSenseRange]:
        """Query all cells' current sense ranges.

        Returns:
            An array of sense ranges, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        ranges = (c_int * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllCellSenseRanges(
                self.__handle, byref(ranges), c_uint(CELL_COUNT))
        self.__check_err(res)
        return [AbsCellSenseRange(r) for r in ranges]

    def enable_cell_noise_filter(self, en: bool):
        """Enable or disable the cell 50/60Hz noise filter.

        This mode filters 50/60Hz noise and increases cell measurement accuracy,
        but decreases the cell control rate to 10Hz.

        Args:
            en: Desired filter state.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_EnableCellNoiseFilter(
                self.__handle, c_bool(en))
        self.__check_err(res)

    def get_cell_noise_filter_enabled(self) -> bool:
        """Query the enable state of the cell 50/60Hz noise filter.

        Returns:
            The state of the noise filter.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        en = c_bool()
        res = self.__dll.AbsScpiClient_GetCellNoiseFilterEnabled(
                self.__handle, byref(en))
        self.__check_err(res)
        return en.value

    def measure_cell_voltage(self, cell: int) -> float:
        """Measure a single cell's voltage.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            Measured cell voltage.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltage = c_float()
        res = self.__dll.AbsScpiClient_MeasureCellVoltage(
                self.__handle, c_uint(cell), byref(voltage))
        self.__check_err(res)
        return voltage.value

    def measure_all_cell_voltages(self) -> list[float]:
        """Measure all cell voltages.

        Returns:
            Array of voltages, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltages = (c_float * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_MeasureAllCellVoltages(
                self.__handle, byref(voltages), c_uint(CELL_COUNT))
        self.__check_err(res)
        return voltages[:]

    def measure_cell_current(self, cell: int) -> float:
        """Measure a single cell's current.

        Args:
            cell: Target cell index, 0-7.

        Returns:
            Measured cell current.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        current = c_float()
        res = self.__dll.AbsScpiClient_MeasureCellCurrent(
                self.__handle, c_uint(cell), byref(current))
        self.__check_err(res)
        return current.value

    def measure_all_cell_currents(self) -> list[float]:
        """Measure all cell currents.

        Returns:
            Array of currents, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        currents = (c_float * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_MeasureAllCellCurrents(
                self.__handle, byref(currents), c_uint(CELL_COUNT))
        self.__check_err(res)
        return currents[:]

    def get_cell_operating_mode(self, cell: int) -> AbsCellMode:
        """Query a single cell's operating mode (constant voltage or current
        limited).

        Args:
            cell: Target cell index, 0-7.

        Returns:
            The cell's operating mode.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        mode = c_int()
        res = self.__dll.AbsScpiClient_GetCellOperatingMode(
                self.__handle, c_uint(cell), byref(mode))
        self.__check_err(res)
        return AbsCellMode(mode.value)

    def get_all_cell_operating_modes(self) -> list[AbsCellMode]:
        """Query all cells' operating modes (constant voltage or current
        limited).

        Returns:
            An array of cell operating modes, one per cell.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        modes = (c_int * CELL_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllCellOperatingModes(
                self.__handle, byref(modes), c_uint(CELL_COUNT))
        self.__check_err(res)
        return [AbsCellMode(m) for m in modes]

    def set_analog_output(self, channel: int, voltage: float):
        """Set a single analog output voltage.

        Args:
            channel: Target channel index, 0-7.
            voltage: Target voltage.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        res = self.__dll.AbsScpiClient_SetAnalogOutput(
                self.__handle, c_uint(channel), c_float(voltage))
        self.__check_err(res)

    def set_all_analog_outputs(self, voltages: list[float]):
        """Set all analog output voltages.

        Args:
            voltages: An array of voltages, one per channel. Must not be empty
                or longer than the total channel count.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        vals = (c_float * len(voltages))(*voltages)
        res = self.__dll.AbsScpiClient_SetAllAnalogOutputs(
                self.__handle, byref(vals), c_uint(len(voltages)))
        self.__check_err(res)

    def get_analog_output(self, channel: int) -> float:
        """Query an analog output's set point.

        Args:
            channel: Target channel index, 0-7.

        Returns:
            The analog output's voltage.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltage = c_float()
        res = self.__dll.AbsScpiClient_GetAnalogOutput(
                self.__handle, c_uint(channel), byref(voltage))
        self.__check_err(res)
        return voltage.value

    def get_all_analog_outputs(self) -> list[float]:
        """Query all analog output voltages.

        Returns:
            An array of voltages, one per channel.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltages = (c_float * ANALOG_OUTPUT_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllAnalogOutputs(
                self.__handle, byref(voltages), c_uint(ANALOG_OUTPUT_COUNT))
        self.__check_err(res)
        return voltages[:]

    def set_digital_output(self, channel: int, level: bool):
        """Set a single digital output.

        Args:
            channel: Target channel index, 0-3.
            level: Desired output level.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        res = self.__dll.AbsScpiClient_SetDigitalOutput(
                self.__handle, c_uint(channel), c_bool(level))
        self.__check_err(res)

    def set_all_digital_outputs(self, levels: list[bool]):
        """Set all digital outputs.

        Args:
            levels: An array of output levels, one per channel. Must not be
                longer than the total channel count.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        if len(levels) > DIGITAL_OUTPUT_COUNT:
            raise ValueError("too many inputs")
        elif len(levels) == 0:
            return

        mask = 0
        for i in range(len(levels)):
            if levels[i]:
                mask |= (1 << i)

        res = self.__dll.AbsScpiClient_SetAllDigitalOutputs(
                self.__handle, c_uint(mask))
        self.__check_err(res)

    def get_digital_output(self, channel: int) -> bool:
        """Query the state of a single digital output.

        Args:
            channel: Target channel index, 0-3.

        Returns:
            The state of the digital output.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        state = c_bool()
        res = self.__dll.AbsScpiClient_GetDigitalOutput(
                self.__handle, c_uint(channel), byref(state))
        self.__check_err(res)
        return state.value

    def get_all_digital_outputs(self) -> list[bool]:
        """Query the states of all digital outputs.

        Returns:
            An array of states, one per output.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        mask = c_uint()
        res = self.__dll.AbsScpiClient_GetAllDigitalOutputs(
                self.__handle, byref(mask))
        self.__check_err(res)
        m = mask.value
        return [(m & (1 << i)) != 0 for i in range(DIGITAL_OUTPUT_COUNT)]

    def measure_analog_input(self, channel: int) -> float:
        """Measure a single analog input.

        Args:
            channel: Target channel index, 0-7.

        Returns:
            Measured voltage.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltage = c_float()
        res = self.__dll.AbsScpiClient_MeasureAnalogInput(
                self.__handle, c_uint(channel), byref(voltage))
        self.__check_err(res)
        return voltage.value

    def measure_all_analog_inputs(self) -> list[float]:
        """Measure all analog inputs.

        Returns:
            An array of voltages, one per channel.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        voltages = (c_float * ANALOG_INPUT_COUNT)()
        res = self.__dll.AbsScpiClient_MeasureAllAnalogInputs(
                self.__handle, byref(voltages), c_uint(ANALOG_INPUT_COUNT))
        self.__check_err(res)
        return voltages[:]

    def measure_digital_input(self, channel: int) -> bool:
        """Measure a single digital input.

        Args:
            channel: Target channel index, 0-3.

        Returns:
            The state of the digital input.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        val = c_bool()
        res = self.__dll.AbsScpiClient_MeasureDigitalInput(
                self.__handle, c_uint(channel), byref(val))
        self.__check_err(res)
        return val.value

    def measure_all_digital_inputs(self) -> list[bool]:
        """Measure all digital inputs.

        Returns:
            An array of states, one per input.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        mask = c_uint()
        res = self.__dll.AbsScpiClient_MeasureAllDigitalInputs(
                self.__handle, byref(mask))
        self.__check_err(res)
        m = mask.value
        return [(m & (1 << i)) != 0 for i in range(DIGITAL_INPUT_COUNT)]

    def get_model_status(self) -> AbsModelStatus:
        """Query the model status bits.

        Returns:
            Model status.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        val = c_uint8()
        res = self.__dll.AbsScpiClient_GetModelStatus(self.__handle, byref(val))
        self.__check_err(res)
        return AbsModelStatus(val.value)

    def load_model(self):
        """Load the model configuration on the device.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        self.__check_err(self.__dll.AbsScpiClient_LoadModel(self.__handle))

    def start_model(self):
        """Start modeling.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        self.__check_err(self.__dll.AbsScpiClient_StartModel(self.__handle))

    def stop_model(self):
        """Stop modeling.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        self.__check_err(self.__dll.AbsScpiClient_StopModel(self.__handle))

    def unload_model(self):
        """Unload the model configuration.

        Raises:
            ScpiClientError: An error occurred while sending the command.
        """
        self.__check_err(self.__dll.AbsScpiClient_UnloadModel(self.__handle))

    def get_model_info(self) -> AbsModelInfo:
        """Query information about the model.

        Returns:
            Model information.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        info = AbsModelInfo()
        res = self.__dll.AbsScpiClient_GetModelInfo(self.__handle, byref(info))
        self.__check_err(res)
        return info

    def set_global_model_input(self, index: int, value: float):
        """Set a single global model input.

        This function is particularly useful with multicast to address multiple
        units.

        Args:
            index: The input index, 0-7.
            value: The input value.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        res = self.__dll.AbsScpiClient_SetGlobalModelInput(
                self.__handle, c_uint(index), c_float(value))
        self.__check_err(res)

    def set_all_global_model_inputs(self, values: list[float]):
        """Set all global model inputs.

        This function is particularly useful with multicast to address multiple
        units.

        Args:
            values: An array of values, one per input. Must not be longer than
                the total input count.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        if len(values) > GLOBAL_MODEL_INPUT_COUNT:
            raise ValueError("too many inputs")
        elif len(values) == 0:
            return

        vals = (c_float * len(values))(*values)
        res = self.__dll.AbsScpiClient_SetAllGlobalModelInputs(
                self.__handle, byref(vals), c_uint(len(values)))
        self.__check_err(res)

    def get_global_model_input(self, index: int) -> float:
        """Query a single global model input.

        Args:
            index: The input index, 0-7.

        Returns:
            The value of the input.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        val = c_float()
        res = self.__dll.AbsScpiClient_GetGlobalModelInput(
                self.__handle, c_uint(index), byref(val))
        self.__check_err(res)
        return val.value

    def get_all_global_model_inputs(self) -> list[float]:
        """Query all global model inputs.

        Returns:
            A list of values, one per input.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        vals = (c_float * GLOBAL_MODEL_INPUT_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllGlobalModelInputs(
                self.__handle, byref(vals), c_uint(GLOBAL_MODEL_INPUT_COUNT))
        self.__check_err(res)
        return vals[:]

    def set_local_model_input(self, index: int, value: float):
        """Set a single local model input.

        Args:
            index: The input index, 0-7.
            value: The input value.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        res = self.__dll.AbsScpiClient_SetLocalModelInput(
                self.__handle, c_uint(index), c_float(value))
        self.__check_err(res)

    def set_all_local_model_inputs(self, values: list[float]):
        """Set all local model inputs.

        Args:
            values: An array of values, one per input. Must not be longer than
                the total input count.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        if len(values) > LOCAL_MODEL_INPUT_COUNT:
            raise ValueError("too many inputs")
        elif len(values) == 0:
            return

        vals = (c_float * len(values))(*values)
        res = self.__dll.AbsScpiClient_SetAllLocalModelInputs(
                self.__handle, byref(vals), c_uint(len(values)))
        self.__check_err(res)

    def get_local_model_input(self, index: int) -> float:
        """Query a single local model input.

        Args:
            index: The input index, 0-7.

        Returns:
            The value of the input.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        val = c_float()
        res = self.__dll.AbsScpiClient_GetLocalModelInput(
                self.__handle, c_uint(index), byref(val))
        self.__check_err(res)
        return val.value

    def get_all_local_model_inputs(self) -> list[float]:
        """Query all local model inputs.

        Returns:
            A list of values, one per input.

        Raises:
            ScpiClientError: An error occurred while executing the command.
        """
        vals = (c_float * LOCAL_MODEL_INPUT_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllLocalModelInputs(
                self.__handle, byref(vals), c_uint(LOCAL_MODEL_INPUT_COUNT))
        self.__check_err(res)
        return vals[:]

    def get_model_output(self, index: int) -> tuple[float, float]:
        """Query a single pair of model outputs.

        Args:
            index: Output index, 0-17.

        Returns:
            The model output pair.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        pair = AbsModelOutputPair()
        res = self.__dll.AbsScpiClient_GetModelOutput(
                self.__handle, c_uint(index), byref(pair))
        self.__check_err(res)
        return pair.to_tuple()

    def get_all_model_outputs(self) -> list[tuple[float, float]]:
        """Query all model output pairs.

        Returns:
            A list of all model output pairs.

        Raises:
            ScpiClientError: An error occurred while executing the query.
        """
        pairs = (AbsModelOutputPair * MODEL_OUTPUT_COUNT)()
        res = self.__dll.AbsScpiClient_GetAllModelOutputs(
                self.__handle, byref(pairs), c_uint(MODEL_OUTPUT_COUNT))
        self.__check_err(res)
        return [p.to_tuple() for p in pairs]

    def multicast_discovery(
        self,
        interface_ip: str,
    ) -> list[AbsEthernetDiscoveryResult]:
        """Use UDP multicast to discover ABSes on the network.

        This function does not require the ScpiClient to be initialized or
        connected.

        Args:
            interface_ip: IP address of the local NIC to bind to.

        Returns:
            List of discovered devices.

        Raises:
            ScpiClientError: An error occurred during discovery.
        """
        results = (AbsEthernetDiscoveryResult * 64)()
        count = c_uint(len(results))
        res = self.__dll.AbsScpiClient_MulticastDiscovery(
                interface_ip.encode(), byref(results), byref(count))
        self.__check_err(res)
        return results[:count.value]

    def serial_discovery(
        self,
        port: str,
        first_id: int = 0,
        last_id: int = 31,
    ) -> list[AbsSerialDiscoveryResult]:
        """Use RS-485 to discover ABSes on the bus.

        This function requires that the ScpiClient *not* be connected over
        serial! This will interfere with opening the serial port.

        Args:
            port: Serial port to use, such as COM1 or /dev/ttyS0.
            first_id: First serial ID to check, 0-31.
            last_id: Last serial ID to check (inclusive), 0-31. Must not be
                less than first_id.

        Returns:
            List of discovered devices.

        Raises:
            ScpiClientError: An error occurred during discovery.
        """
        if last_id < 0 or last_id > 31 or first_id < 0 or first_id > 31:
            raise ValueError("invalid ID")
        elif last_id < first_id:
            raise ValueError("last ID cannot be less than first ID")

        count = c_uint(last_id - first_id + 1)
        results = (AbsSerialDiscoveryResult * count.value)()
        res = self.__dll.AbsScpiClient_SerialDiscovery(
                port.encode(), c_uint8(first_id), c_uint8(last_id),
                byref(results), byref(count))
        self.__check_err(res)
        return results[:count.value]

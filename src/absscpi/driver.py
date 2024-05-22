from ctypes import *
from ctypes.util import find_library
import platform

LIB_NAME = "absscpi"

class AbsDeviceInfo(Structure):
    _fields_ = [("part_number", c_char * 128),
                ("serial", c_char * 128),
                ("version", c_char * 128)]

    def get_part_number(self) -> str:
        return self.part_number.decode()

    def get_serial(self) -> str:
        return self.serial.decode()

    def get_version(self) -> str:
        return self.version.decode()

class AbsEthernetConfig(Structure):
    _fields_ = [("ip", c_char * 32),
                ("netmask", c_char * 32)]

    def get_ip_address(self) -> str:
        return self.ip.decode()

    def get_netmask(self) -> str:
        return self.netmask.decode()

class AbsEthernetDiscoveryResult(Structure):
    _fields_ = [("ip", c_char * 32),
                ("serial", c_char * 128)]

    def get_ip_address(self) -> str:
        return self.ip.decode()

    def get_serial(self) -> str:
        return self.serial.decode()

class ScpiClientError(Exception):
    pass

class ScpiClient:
    def __init__(self, lib: str = LIB_NAME):
        self.__handle = c_void_p()

        if platform.system() == "Windows":
            load_library_func = windll.LoadLibrary
        else:
            load_library_func = cdll.LoadLibrary

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

    def err_msg(self, err: int) -> str:
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
            raise ScpiClientError(self.err_msg(err))

    def init(self):
        """Initialize the client handle.

        Should not be called directly! Use a "with" block instead:

            with ScpiClient() as client:
                ...

        Raises:
            ScpiClientError: An error occurred during initialization.
        """
        res = self.__dll.AbsScpiClient_Init(byref(self.__handle))
        self.__check_err(res)

    def cleanup(self):
        """Cleanup the client handle.

        Should not be called directly! Use a "with" block instead:

            with ScpiClient() as client:
                ...
        """
        self.__dll.AbsScpiClient_Destroy(byref(self.__handle))

    def open_udp(self, target_ip: str, interface_ip: str | None = None):
        """Open a UDP socket to communicate with the device.

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

    def open_serial(self, port: str, device_id: int):
        """Open a serial connection to the device.

        Args:
            port: Serial port, such as "COM1" or "/dev/ttyS1."
            device_id: Device's serial ID, 0-255, or 256+ to address all units
                on the bus.

        Raises:
            ScpiClientError: An error occurred while opening the port.
        """
        if device_id < 0:
            raise ValueError(f"device ID out of range: {device_id}")
        res = self.__dll.AbsScpiClient_OpenSerial(
                self.__handle, port.encode(), c_uint(device_id))
        self.__check_err(res)

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
        buf = create_string_buffer(128)
        res = self.__dll.AbsScpiClient_GetCalibrationDate(
                self.__handle, byref(buf), c_uint(len(buf)))
        self.__check_err(res)
        return buf.value.decode()

    def get_error_count(self) -> int:
        count = c_int()
        res = self.__dll.AbsScpiClient_GetErrorCount(
                self.__handle, byref(count))
        self.__check_err(res)
        return count.value

    def get_next_error(self) -> tuple[int, str]:
        buf = create_string_buffer(256)
        code = c_int16()
        res = self.__dll.AbsScpiClient_GetNextError(
                self.__handle, byref(code), byref(buf), c_uint(len(buf)))
        self.__check_err(res)
        return (code.value, buf.value.decode())

    def clear_errors(self):
        res = self.__dll.AbsScpiClient_ClearErrors(self.__handle)
        self.__check_err(res)

    def set_cell_voltage(self, cell: int, voltage: float):
        res = self.__dll.AbsScpiClient_SetCellVoltage(
                self.__handle, c_uint(cell), c_float(voltage))
        self.__check_err(res)

    def set_all_cell_voltages(self, voltages: list[float]):
        vals = (c_float * len(voltages))(*voltages)
        res = self.__dll.AbsScpiClient_SetAllCellVoltages(
                self.__handle, byref(vals), c_uint(len(voltages)))
        self.__check_err(res)

    def get_cell_voltage_target(self, cell: int) -> float:
        voltage = c_float()
        res = self.__dll.AbsScpiClient_GetCellVoltageTarget(
                self.__handle, c_uint(cell), byref(voltage))
        self.__check_err(res)
        return voltage.value

    def get_all_cell_voltage_targets(self) -> list[float]:
        voltages = (c_float * 8)()
        res = self.__dll.AbsScpiClient_GetAllCellVoltageTargets(
                self.__handle, byref(voltages), c_uint(8))
        self.__check_err(res)
        return voltages[:]

    def multicast_discovery(
        self,
        interface_ip: str,
    ) -> list[AbsEthernetDiscoveryResult]:
        results = (AbsEthernetDiscoveryResult * 32)()
        count = c_uint(len(results))
        res = self.__dll.AbsScpiClient_MulticastDiscovery(
                interface_ip.encode(), byref(results), byref(count))
        self.__check_err(res)
        return results[:count.value]

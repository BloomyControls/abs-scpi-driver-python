# Copyright (c) 2024, Bloomy Controls, Inc. All rights reserved.
#
# Use of this source code is governed by a BSD-3-clause license that can be
# found in the LICENSE file or at https://opensource.org/license/BSD-3-Clause

"""
ABS SCPI client module.

This ``absscpi`` module provides a SCPI client for communicating with the Bloomy
Controls Advanced Battery Simulator through TCP, UDP, RS-485, and UDP multicast.
"""

__version__ = "0.1.0"

__all__ = [
    "AbsCellFault",
    "AbsCellSenseRange",
    "AbsCellMode",
    "AbsDeviceInfo",
    "AbsEthernetConfig",
    "AbsModelStatus",
    "AbsModelInfo",
    "AbsEthernetDiscoveryResult",
    "AbsSerialDiscoveryResult",
    "ScpiClientError",
    "ScpiClient",
]

from .client import (
    AbsCellFault,
    AbsCellSenseRange,
    AbsCellMode,
    AbsDeviceInfo,
    AbsEthernetConfig,
    AbsModelStatus,
    AbsModelInfo,
    AbsEthernetDiscoveryResult,
    AbsSerialDiscoveryResult,
    ScpiClientError,
    ScpiClient,
)

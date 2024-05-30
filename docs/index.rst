absscpi
=======

The **absscpi** library provides a fully-featured Python driver for the Bloomy
Controls ABS over TCP, UDP, RS-485, and UDP multicast. This library is a wrapper
around the `native C/C++ SCPI driver <native_>`_ for the ABS to avoid
unnecessary Python performance overhead.

A simple example showing how to connect to an ABS over UDP and control and
measure one cell:

.. literalinclude:: ../examples/single_cell.py
   :language: python
   :linenos:

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   installation
   client
   util
   development

Known Bugs
==========

See the `bug tracker`_ on GitHub. Contributions welcome!

.. admonition:: Documentation generated

   |today|

.. _native: https://github.com/BloomyControls/abs-scpi-driver
.. _bug tracker: https://github.com/BloomyControls/abs-scpi-driver-python/issues

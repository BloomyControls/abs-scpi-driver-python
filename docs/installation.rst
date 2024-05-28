Installation
============

Install the ``absscpi`` package from PyPI with ``pip`` or similar::

    $ pip install absscpi

The Python library depends on the native C/C++ library. For instructions on
installing it, see :ref:`native-installation`.

.. _native-installation:

C/C++ driver installation
-------------------------

This library depends on the `native C/C++ library <native_>`_. First, download
the appropriate zip file for your platform from the `latest release`_.

Windows
^^^^^^^

For the Python library to automatically find the driver DLL, copy the downloaded
DLLs to :file:`C:/Windows/System32`.

If you do not have administrator privileges or would prefer not to place files
in :file:`System32` for some other reason, you may place the DLLs wherever you
like. For details, see :ref:`custom-location`.

Linux
^^^^^

For most systems, directly copying the downloaded directories into
:file:`/usr/local` should do the trick. It's not advised to directly install
the driver into :file:`/usr`, as your system package manager should be in charge
of that. For example::

    $ sudo cp -r include lib* /usr/local/

If you wish to install the library to a custom location, see
:ref:`custom-location`.

.. _custom-location:

Using a custom install location
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you choose to install the library to a custom location and
:func:`~absscpi.ScpiClient` doesn't automatically find it, you can manually tell
it where you put the library. For example:

.. code-block:: python

   # Windows:
   with ScpiClient(lib="C:/Users/me/path/to/absscpi.dll") as client:
       pass

   # Linux:
   with ScpiClient(lib="/home/me/path/to/libabsscpi.so") as client:
       pass

Linux alternative: using ``LD_LIBRARY_PATH``
""""""""""""""""""""""""""""""""""""""""""""

On Linux, there is an alternative to the above example which leaves your Python
code unchanged (and therefore keeps it portable) but still allows you to install
the library wherever you please: ``LD_LIBRARY_PATH``.

As long as the directory containing :file:`libabsscpi.so` is present in the
``LD_LIBRARY_PATH`` environment variable, :func:`~absscpi.ScpiClient` should be
able to find it and load it automatically.

For more information, see :manpage:`ld.so(8)`.

.. _native: https://github.com/BloomyControls/abs-scpi-driver
.. _latest release:
   https://github.com/BloomyControls/abs-scpi-driver/releases/latest

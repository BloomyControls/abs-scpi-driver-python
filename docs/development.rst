Developer's Overview
====================

Contributing
------------

You can contribute to the project or report issues on the GitHub repository:
https://github.com/BloomyControls/abs-scpi-driver-python

Remember, the Python library is a thin wrapper around the C/C++ drivers. If you
have a problem/feature request pertaining to the C/C++ drivers, you should
contribute that directly to the C/C++ drivers:
https://github.com/BloomyControls/abs-scpi-driver

Building and Installing
-----------------------

Before doing any of the commands below, you should setup a `virtual
environment <venv_>`_:

.. tab:: Windows (PowerShell)

   .. code-block::

      python -m venv .venv
      .venv\Scripts\Activate.ps1

.. tab:: Linux

   .. code-block::

      python -m venv .venv
      . .venv/bin/activate

To install requirements for building::

    python -m pip install -r dev-requirements.txt

To install the project locally from source::

    python -m pip install .

To build HTML documentation::

    python -m pip install -r docs/doc-requirements.txt
    python -m sphinx -an docs docs/_build


Creating a New Release
----------------------

- Always release from the ``main`` branch.
- Update the version, either using ``hatch version`` or by manually editing
  ``__init__.py``.
- Build distribution package: ``python -m build``.

.. todo::

   Finish this documentation when release packaging/uploading is sorted out.

.. _venv: https://docs.python.org/3/library/venv.html

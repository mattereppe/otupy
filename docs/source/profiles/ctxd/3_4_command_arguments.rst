3.4 Command Arguments
=====================

The CTXD extension adds the following arguments:

.. list-table:: CTXD-specific arguments
   :header-rows: 1

   * - Name
     - Type
     - Meaning
   * - ``name_only``
     - ``bool``
     - Request the lightweight/name-oriented behavior supported by an implementation.
   * - ``cached``
     - ``bool``
     - Allow cached context information to be used instead of forcing a refresh.

The command validator currently accepts these argument combinations:

.. list-table:: CTXD argument matrix
   :header-rows: 1

   * - Command
     - Accepted arguments
   * - ``query features``
     - ``response_requested``
   * - ``query x-ctxd:context``
     - ``name_only``, ``cached``

.. note::
   ``Args`` inherits the common OpenC2 arguments, but the current CTXD
   validation table does **not** accept ``response_requested`` for
   ``query x-ctxd:context``.

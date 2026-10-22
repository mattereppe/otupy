3.4 Command Arguments
=====================

XBOM extends the common OpenC2 arguments with:

.. list-table:: XBOM-specific arguments
   :header-rows: 1

   * - Name
     - Type
     - Meaning
   * - ``format``
     - :py:class:`~otupy.profiles.xbom.data.xbom_format.XbomFormat`
     - Requested BOM data model, currently ``ctxd`` or ``cyclonedx``.
   * - ``encoding``
     - :py:class:`~otupy.profiles.xbom.data.xbom_encoding.XbomEncoding`
     - Requested serialization, currently ``json``, ``xml``, or ``yaml``.
   * - ``cached``
     - ``bool``
     - Allow cached BOM information to be returned.

The current validator accepts ``response_requested`` for ``query features``.
For ``query x-xbom:boms`` it accepts ``response_requested``, ``cached``,
``format``, and ``encoding``.

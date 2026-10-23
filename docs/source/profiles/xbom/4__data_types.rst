4. XBOM Data Types
==================

This section defines the data types used by the XBOM Command and Response
extensions and summarizes the object model from which XBOM representations are
constructed. The Command and Response exchange carries serialized BOM strings;
the model types in later subsections describe the structured data that can be
used to create those strings.

References to a type name use the type label itself as a link to the
corresponding inline code documentation.

.. _xbom-type-boms:

4.1 XbomTarget
--------------

``XbomTarget`` is the value of the profile-defined ``boms`` target. It is a
list of component identifiers; a zero-length list asks for all BOMs available
through the addressed Consumer.

.. rubric:: Type: :py:class:`XbomTarget <otupy.profiles.xbom.targets.xbom_ctx.XbomTarget>` (ArrayOf(String))

.. list-table:: Table 4.1-1. XbomTarget Data Type
   :header-rows: 1
   :widths: 25 25 50

   * - Name
     - Type
     - Description
   * - ``boms``
     - ArrayOf(String)
     - Zero or more component identifiers that select the BOMs to retrieve.
       The identifiers have no additional format constraint in the profile.

.. _xbom-type-xbom-format:

4.2 XbomFormat
--------------

``XbomFormat`` identifies the data model used to express a BOM.

.. rubric:: Type: :py:class:`XbomFormat <otupy.profiles.xbom.data.xbom_format.XbomFormat>` (Enumerated)

.. list-table:: Table 4.2-1. XbomFormat Values
   :header-rows: 1
   :widths: 15 25 60

   * - ID
     - Name
     - Description
   * - 0
     - ``ctxd``
     - otupy native data model for context discovery.
   * - 1
     - ``cyclonedx``
     - CycloneDX data model for application security context and software
       supply-chain component analysis.

.. _xbom-type-xbom-encoding:

4.3 XbomEncoding
----------------

``XbomEncoding`` identifies the serialization encoding used to transport a BOM
as a string. An actuator selects only encodings that it supports for the
requested format.

.. rubric:: Type: :py:class:`XbomEncoding <otupy.profiles.xbom.data.xbom_encoding.XbomEncoding>` (Enumerated)

.. list-table:: Table 4.3-1. XbomEncoding Values
   :header-rows: 1
   :widths: 15 25 60

   * - ID
     - Name
     - Description
   * - 0
     - ``json``
     - JavaScript Object Notation encoding.
   * - 1
     - ``xml``
     - Extensible Markup Language encoding.
   * - 2
     - ``yaml``
     - YAML serialization.



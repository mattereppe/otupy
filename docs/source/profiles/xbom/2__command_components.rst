2. Command Components
=====================

This section identifies the OpenC2 Actions, Targets, Command Arguments, and
Actuator Specifiers that are meaningful for the eXtended Bill of Materials
(XBOM) profile. XBOM reuses the common OpenC2 ``query`` Action and extends the
language with a BOM target, retrieval arguments, and routing specifiers.

2.1 Actions
-----------

2.1.1 Common Actions
^^^^^^^^^^^^^^^^^^^^

XBOM does not define new Actions. The following Action from the OpenC2 Language
Specification is applicable to the profile. The permitted Action--Target pairs
are defined in :ref:`xbom-command-matrix`.

.. rubric:: Type: Action (Enumerated)

.. list-table:: Table 2.1.1-1. Common Actions Applicable to XBOM
   :header-rows: 1
   :widths: 15 25 60

   * - ID
     - Name
     - Description
   * - 3
     - ``query``
     - Request supported OpenC2 features or retrieve one or more XBOM
       representations.

2.2 Targets
-----------

2.2.1 Common Targets
^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.1-1. Common Targets Applicable to XBOM
   :header-rows: 1
   :widths: 15 25 22 38

   * - ID
     - Name
     - Type
     - Description
   * - 9
     - ``features``
     - Features
     - Requests the common OpenC2 capabilities supported by the addressed
       Consumer and XBOM actuator.

2.2.2 Targets Unique to XBOM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Target is defined by the XBOM profile. In this profile document,
the target is shown without the ``x-xbom`` namespace prefix; the prefix is used
in the serialized OpenC2 Command.

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.2-1. Targets Unique to XBOM
   :header-rows: 1
   :widths: 25 25 10 40

   * - Name
     - Type
     - #
     - Description
   * - ``boms``
     - :ref:`XbomTarget <xbom-type-boms>`
     - 1
     - Requests BOMs. The array can identify specific components; an empty
       array requests every BOM available to the Consumer.

2.3 Command Arguments
---------------------

2.3.1 Common Arguments
^^^^^^^^^^^^^^^^^^^^^^

The XBOM validation rules permit ``response_requested`` for both valid Query
targets. Other common Command Arguments are not permitted by the current
profile implementation.

.. rubric:: Type: Args (Map)

.. list-table:: Table 2.3.1-1. Common Command Arguments Applicable to XBOM
   :header-rows: 1
   :widths: 15 28 22 10 25

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 4
     - ``response_requested``
     - Response-Type
     - 0..1
     - Requested response level: ``none``, ``ack``, ``status``, or
       ``complete``.

2.3.2 Arguments Unique to XBOM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following arguments control the representation and freshness of the BOMs
returned by ``query boms``.

.. rubric:: Type: :py:class:`Args <otupy.profiles.xbom.args.Args>` (Map)

.. list-table:: Table 2.3.2-1. Command Arguments Unique to XBOM
   :header-rows: 1
   :widths: 25 25 10 40

   * - Name
     - Type
     - #
     - Description
   * - ``format``
     - :ref:`XbomFormat <xbom-type-xbom-format>`
     - 0..1
     - Requested BOM data model, such as ``ctxd`` or ``cyclonedx``.
   * - ``encoding``
     - :ref:`XbomEncoding <xbom-type-xbom-encoding>`
     - 0..1
     - Requested serialization encoding. The selected encoding must be
       supported by the requested format, when one is supplied.
   * - ``cached``
     - Boolean
     - 0..1
     - If true, permits a cached answer. If false or omitted, the Consumer
       updates component information before returning the response.

2.4 Actuator Specifiers
-----------------------

XBOM defines the following Actuator Specifiers. ``asset_id`` is an opaque
routing identifier: it selects the Consumer-side XBOM actuator instance but
does not change the XBOM language semantics. The current profile implementation
does not apply additional interpretation to ``domain``.

.. rubric:: Type: :py:class:`Specifiers <otupy.profiles.xbom.actuator.Specifiers>` (Map)

.. list-table:: Table 2.4-1. XBOM Actuator Specifiers
   :header-rows: 1
   :widths: 25 20 10 45

   * - Name
     - Type
     - #
     - Description
   * - ``domain``
     - String
     - 0..1
     - Optional profile-defined string used to distinguish the addressed XBOM
       context or administrative scope.
   * - ``asset_id``
     - String
     - 0..1
     - Opaque identifier of the XBOM actuator instance that executes the
       Command.

.. _xbom-command-matrix:

2.5 Command Matrix
------------------

An Action in the top row paired with a Target in the first column defines a
valid XBOM Command.

.. list-table:: Table 2.5-1. XBOM Command Matrix
   :header-rows: 1
   :widths: 45 45

   * - Target
     - ``query``
   * - ``features``
     - valid
   * - ``boms``
     - valid

2.6 Command Arguments Matrix
----------------------------

An Argument in the first column is permitted for the Query Command shown in the
corresponding top-row column.

.. list-table:: Table 2.6-1. XBOM Command Arguments Matrix
   :header-rows: 1
   :widths: 34 33 33

   * - Argument
     - ``query features``
     - ``query boms``
   * - ``response_requested``
     - valid
     - valid
   * - ``format``
     -
     - valid
   * - ``encoding``
     -
     - valid
   * - ``cached``
     -
     - valid


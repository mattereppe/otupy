3.2 Target
==========

Target is a mandatory field in Command message, and it is possible to
define new Targets that are not present in the specifications. Only one
Target is allowed in a Command, and that's why the cardinality of each
one equals to 1.

Type: :py:class:`~otupy.core.target.Target` (:py:class:`~otupy.types.base.choice.Choice`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 9
     - features
     - :py:class:`~otupy.types.targets.features.Features`
     - 1
     - A set of items used with the query Action to determine an Actuator's capabilities.
   * - 10
     - xbom
     - :py:class:`~otupy.profiles.xbom.targets.xbom_ctx.XbomCtx`
     - 1
     - It describes the service environment, its connections and security capabilities in a BOM standard compliant format.

A new target, called "xbom", is introduced because the Target "features"
refers only to the Actuator capabilities and not to the characteristics
of the execution environment.

The "xbom" Target returns the service environment in a Bill of Materials
standard compliant format, such as CycloneDX.

.. note::

   The previous target name "context" (class ``Context``) has been deprecated.
   Use the "xbom" target (class :py:class:`~otupy.profiles.xbom.targets.xbom_ctx.XbomCtx`) instead.
   The ``Context`` class is kept as an alias for backward compatibility.


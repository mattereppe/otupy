4.2 Common Results
==================

This section refers to the Results that are meaningful in the context of
a CTXD and that are listed in the Language Specification.

Type: :py:class:`~otupy.core.results.Results` (:py:class:`~otupy.types.base.record.Record`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - versions
     - :py:class:`~otupy.types.data.version.Version` 
     - 0
     - List of OpenC2 language versions supported by this Actuator.
   * - 2
     - profiles
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.types.data.nsid.Nsid`)
     - 0
     - List of profiles supported by this Actuator.
   * - 3
     - action-targets
     - :py:class:`~otupy.core.actions.Actions`-:py:class:`~otupy.core.target.Target`
     - 0
     - List of targets applicable to each supported Action.
   * - 4
     - rate_limit
     - ``int``\{0..*}
     - 0
     - Maximum number of requests per minute supported by design or policy.
   * - 1
     - slpf
     - slpf::py:class:`~otupy.profiles.slpf.results.Results`
     - 0
     - Example: Result properties defined in the Stateless Packet Filtering Profile.


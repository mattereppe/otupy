3.3 BOM target
==============

Type: :py:class:`~otupy.profiles.xbom.targets.xbom_ctx.XbomTarget`
(``ArrayOf(str)``)

The ``x-xbom:boms`` target optionally carries component identifiers:

* with no identifiers, the Consumer is asked for all available BOMs;
* with one or more identifiers, only BOMs for those components are requested.

Format and serialization are **not** target fields. They are selected through
the ``format`` and ``encoding`` command arguments.

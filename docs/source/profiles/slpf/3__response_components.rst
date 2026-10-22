3. Response Components
======================

SLPF extends the common OpenC2 ``Results`` object with ``rule_number``, a
:py:class:`~otupy.profiles.slpf.targets.rule_id.RuleID` identifying a rule
created or managed by the packet filter.

The current implementation accepts status codes ``102`` Processing, ``200`` OK,
``400`` Bad Request, ``500`` Internal Error, and ``501`` Not Implemented.

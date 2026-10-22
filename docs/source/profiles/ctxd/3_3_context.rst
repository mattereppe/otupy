3.3 Context target
==================

Type: :py:class:`~otupy.profiles.ctxd.targets.context.Context`

The current ``Context`` target is an empty record. Earlier versions exposed
``services`` and ``links`` selectors, but those fields have been removed from
the active implementation. A ``query x-ctxd:context`` command therefore asks
for the current context as a whole; filtering behavior belongs outside the
current target schema.

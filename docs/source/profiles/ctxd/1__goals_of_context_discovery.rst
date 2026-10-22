1. Goals of Context Discovery
=============================

CTXD provides a profile-level interface for retrieving a description of the
execution environment visible to a Consumer. The returned context is expressed
as services and links between services. A Producer can use this information to
build a wider topology by querying additional Consumers when appropriate.

The profile namespace identifier is ``x-ctxd`` and the profile name in the
implementation is ``Context Discovery``.

The current implementation supports the ``query`` action for the standard
``features`` target and for the profile-specific ``x-ctxd:context`` target.

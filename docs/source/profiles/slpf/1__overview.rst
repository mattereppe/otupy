1. Overview
===========

SLPF controls stateless packet-filtering rules. The ``otupy`` implementation
uses the standard OpenC2 actions ``allow``, ``deny``, ``query``, ``update``, and
``delete`` and adds the profile-specific ``slpf:rule_number`` target and SLPF
arguments.

The active validation matrix currently enables IPv4 connection/network targets
for ``allow`` and ``deny``. IPv6 targets are mentioned in the source module but
are commented out of the active command matrix, so they are not documented as
implemented here.

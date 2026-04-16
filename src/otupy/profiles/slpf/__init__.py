""" StateLess Packet Filter profile

	This module collects all public definition that are exported as part of the SLPF profile.
	All naming follows as much as possible the terminology in the SLPF Specification, by
	also applying generic ~otupy conventions.

	This definition also registers all extensions defined in the SLPF profile (`Args`, `Target`, `Profile`, `Results`).

	The SLPF profile extends the language specification with the following elements:

	- :py:class:`~otupy.core.profile.Profile`:

		- :py:class:`~otupy.profiles.slpf.profile.Profile` profile is defined for all Actuators that will implement it;
		- :py:class:`~otupy.profiles.slpf.profile.nsid` is defined as Namespace identifier for the SLPF profile;

	- :py:class:`~otupy.types.data`:

		- :py:class:`~otupy.profiles.slpf.data.direction.Direction` is used to specify the rule applies to incoming, outgoing, or both kinds of packets;
	- :py:class:`~otupy.types.targets`:
	
		- :py:class:`~otupy.profiles.slpf.targets.rule_id.RuleID` identifies a rule identifier to distinguish firewalling rules;
		
	- :py:class:`~otupy.core.target.Target`:

		- :py:class:`~otupy.profiles.slpf.targets.rule_id.RuleID` is the identifier of an SLPF rule;

	- :py:class:`~otupy.core.args.Args`:

		- :py:class:`~otupy.profiles.slpf.args.Args` is extended with ``drop_process``, ``persistent``, ``direction``, and ``insert_rule`` arguments;
	- :py:class:`~otupy.core.results.Results`:

		- :py:class:`~otupy.profiles.slpf.results.Results` is extended with the ``rule_id`` field;

	- validation:

		- :py:class:`~otupy.profiles.slpf.validation.AllowedCommandTarget` contains all valid :py:class:`~otupy.core.target.Target` for each :py:class:`~otupy.core.actions.Actions`;
		- :py:class:`~otupy.profiles.slpf.validation.AllowedCommandArguments` contains all valid :py:class:`~otupy.core.args.Args` for each < :py:class:`~otupy.core.actions.Actions`, :py:class:`~otupy.core.target.Target` > pair;

	- helper functions:

		- :py:class:`~otupy.profiles.slpf.validation.validate_command` checks a < :py:class:`~otupy.core.target.Target` , :py:class:`~otupy.core.actions.Actions` > pair in a :py:class:`~otupy.core.command.Command` is present in :py:class:`~otupy.profiles.slpf.validation.AllowedCommandTarget`;
		- :py:class:`~otupy.profiles.slpf.validation.validate_args` checks a < :py:class:`~otupy.core.args.Args` , :py:class:`~otupy.core.actions.Actions` , :py:class:`~otupy.core.target.Target` > triple in a :py:class:`~otupy.core.command.Command` is present in :py:class:`~otupy.profiles.slpf.validation.AllowedCommandArguments`.	


"""


from otupy.profiles.slpf.profile import Profile, nsid
from otupy.profiles.slpf.actuator import *

from otupy import TargetEnum
from otupy.profiles.slpf.data import Direction
from otupy.profiles.slpf.targets import RuleID


# According to the standard, extended targets must be prefixed with the nsid
from otupy.profiles.slpf.args import Args
from otupy.profiles.slpf.results import Results
from otupy.profiles.slpf.validation import AllowedCommandTarget, AllowedCommandArguments, validate_command, validate_args

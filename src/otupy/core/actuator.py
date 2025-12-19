"""OpenC2 Actuator

This module defines the `Actuator` element. There are two concepts of Actuator in otupy. First, according to the Language
Specification, an `Actuator` specifier is used to identify the subject of Commands. It is used to identify the Actuator that
will run the command, including its Actuator Profiles. 
Second, Actuator in otupy is also used to provide the concrete implementation of an Actuator Manager. Usually, an Actuator 
implements a Profile for a specific security function (e.g.: Stateless Packet Filter for iptables). 

A base class is only provided for the specifier. For actuator implementations, a decorator is provided that keeps track
of all provided implementations.

"""

import aenum

from otupy.types.base  import Choice
from otupy.core.extensions import Extensions, Register

Extensions['Actuators'] = Register()
""" A list of Specifiers for the different Actuator Profiles. Note that the terminology `Actuator` is only used
	to remain fully compliant with the Language Specification. In more practical terms (according to the otupy
	approch), these are (Actuator) Profiles extensions.
"""

Actuators = Register()
""" These are indeed the different implementations available of Actuators. A single implementation might implement
	multiple Profiles, but this is not relevant to Consumers, so we do not track it. Overall, each Actuator implementation
	is expected to check the command before executing it, and verify if it is compliant with the implemented Profiles.
"""


class Actuator(Choice):
	"""OpenC2 Actuator Specifier
	
	The `Actuator` object carries a Specifier which identifies an implementation of the Profile to which the Command applies, 
	according to the definition in Sec. 3.3.1.3 of the 
	Language Specification. However, note that this `Actuator` definition is fully transparent to its concrete implementation 
	for a specific security functions.
	"""
	register = Extensions['Actuators']
	""" Registry of available `Actuator`

		For internal use only. Do not change or alter.
	"""


def actuator(nsid):
	""" The `@actuator` decorator

		Use this decorator to declare an `Actuator` in otupy extensions.

		:param nsid: The Profile NameSpace identifier (must be the same as defined by the corresponding Profile specification.
		:result: The following class definition is registered as valid `Actuator` in otupy.
	"""
	def actuator_registration(cls):
		Extensions['Actuators'].add(nsid, cls)
		return cls
	return actuator_registration

def actuator_implementation(name):
	""" The `@actuator_implementation` decorator.

		Use this decorator to declare the implementation of an Actuator. Beware not confuse this decorator with the one for
		declaring an Actuator Profile specifier. 
		Use this decorator to declare the implementation of an `Actuator`. The implementation is identified by its name,
		which should be something meaningful to identify the scope (security function and Profile) of the implementation.
		There is no need to declare here the profile(s) implemented by this Actuator,
		since this remains fully trasparent to the Consumer.

		:param name: The name for this Actuator implementation.
		:result: The following class definition is registered as available `Actuator` implementation in otupy.
	"""
	def implementation_registration(cls):
		Actuators.add(name, cls)
		return cls
	return implementation_registration




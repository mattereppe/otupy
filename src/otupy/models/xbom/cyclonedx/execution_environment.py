from otupy.models.ctxd.execution_environment import ExecutionEnvironment

from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from otupy.models.xbom.cyclonedx.bom_ref import generate_bom_ref

def to_cyclonedx(self) -> Component:
	"""Convert ExecutionEnvironment to CycloneDX component format.
	
	Returns:
		Component: CycloneDX Component with type PLATFORM and nested components.
	"""
	properties = [
		Property(name="otupy:type", value="execution_environment")
	]
	if self.id is not None:
		properties.append(Property(name="otupy:execenv:id", value=str(self.id)))
	if self.version is not None:
		properties.append(Property(name="otupy:execenv:version", value=self.version))
	
	# Add nested components (applications, libraries, packages)
	nested_components = []
	if self.apps is not None:
		for app in self.apps:
			nested_components.append(app.to_cyclonedx())
	if self.libs is not None:
		for lib in self.libs:
			nested_components.append(lib.to_cyclonedx())
	if self.pkgs is not None:
		for pkg in self.pkgs:
			nested_components.append(pkg.to_cyclonedx())

	exec_env_tmp = Component(
			name=self.name or "unknown",
			type=ComponentType.PLATFORM,
			bom_ref=generate_bom_ref("execenv"),
			description=self.description,
			properties=properties,
			components=nested_components if nested_components else None
		)
	
	# Recusively get the bom representation
	exec_env = self.type.getObj() if self.type is not None else None
	if exec_env is not None and hasattr(exec_env, 'to_cyclonedx'):
		exec_env_cdx = exec_env.to_cyclonedx()
		if exec_env_cdx is not None:
			# Add name and description from current component
			exec_env_cdx.name = exec_env_cdx.name or exec_env_tmp.name
			exec_env_cdx.description = exec_env_cdx.description or exec_env_tmp.description
			nested_type = None
			if exec_env_cdx.properties is not None:
				for prop in exec_env_cdx.properties:
					if getattr(prop, "name", None) == "otupy:type":
						nested_type = getattr(prop, "value", None)
						break
			if nested_type is not None:
				exec_env_cdx.properties.add(Property(name=nested_type+"id", value=self.id))
			if self.version is not None:
				exec_env_cdx.properties.add(Property(name=nested_type+"version", value=self.version))
			if exec_env_cdx.components is not None:
				for component in nested_components:
					exec_env_cdx.components.add(component)
			else:
				exec_env_cdx.components = nested_components if nested_components else None
			return exec_env_cdx
		else:
			return exec_env_tmp
	else:
		return exec_env_tmp
	
ExecutionEnvironment.to_cyclonedx = to_cyclonedx

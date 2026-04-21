from nomad.config.models.plugins import SchemaPackageEntryPoint

class MagnetometrySchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_measurements_magnetometry.schema_packages.vsm_schema import m_package as vsm_pkg
        from nomad_measurements_magnetometry.schema_packages.agm_schema import m_package as agm_pkg

        return vsm_pkg, agm_pkg


schema_package_entry_point = MagnetometrySchemaPackageEntryPoint(
    name='Magnetometry Schemas',
    description='Schemas for Magnetometry (VSM, AGM, etc) data.',
)

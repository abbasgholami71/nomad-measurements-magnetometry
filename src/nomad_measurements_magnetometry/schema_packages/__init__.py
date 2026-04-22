from nomad.config.models.plugins import SchemaPackageEntryPoint


class AGMSchemaEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from .agm_schema import m_package

        return m_package


class VSMSchemaEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from .vsm_schema import m_package

        return m_package


agm_schema_entry_point = AGMSchemaEntryPoint(
    name='AGM Schema',
    description='Schema for MicroMag AGM data.',
)

vsm_schema_entry_point = VSMSchemaEntryPoint(
    name='VSM Schema',
    description='Schema for Lake Shore VSM data.',
)

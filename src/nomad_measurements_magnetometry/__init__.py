from nomad.config.models.plugins import SchemaPackageEntryPoint

class MagnetometrySchemaEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from .schema_packages import m_package
        return m_package

magnetometry_schema_entry_point = MagnetometrySchemaEntryPoint(
    name='Magnetometry Schema',
    description='Schema for Magnetometry exported data files.',
)
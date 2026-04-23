import numpy as np
from nomad.datamodel.data import ArchiveSection
from nomad.datamodel.metainfo.basesections import Measurement, MeasurementResult
from nomad.metainfo import Quantity, Section, SubSection, SchemaPackage

m_package = SchemaPackage()

class MagnetometrySample(ArchiveSection):
    sample_id = Quantity(type=str)
    mass = Quantity(type=np.float64, unit='g')
    volume = Quantity(type=np.float64, unit='cm**3')
    area = Quantity(type=np.float64, unit='cm**2')
    density = Quantity(type=np.float64, unit='g/cm**3')
    thickness = Quantity(type=np.float64, unit='mm')
    demagnetizing_factor = Quantity(type=np.float64, description='Generic or SI demagnetizing factor')
    demagnetizing_factor_cgs = Quantity(type=np.float64, description='CGS demagnetizing factor')

class MagnetometryResult(MeasurementResult):
    magnetic_field = Quantity(type=np.float64, shape=['*'], description='Applied magnetic field (Oe)')
    magnetic_moment = Quantity(type=np.float64, shape=['*'], description='Measured magnetic moment (emu)')
    normalized_moment = Quantity(type=np.float64, shape=['*'], description='Moment normalized by mass/volume')
    time_stamp = Quantity(type=np.float64, shape=['*'], unit='s')
    step_array = Quantity(type=np.int32, shape=['*'])
    iteration_array = Quantity(type=np.int32, shape=['*'])
    segment_array = Quantity(type=np.int32, shape=['*'])
    field_status = Quantity(type=str, shape=['*'])
    moment_status = Quantity(type=str, shape=['*'])

class BaseMagnetometry(Measurement):
    instrument_model = Quantity(type=str)
    software_version = Quantity(type=str)
    measurement_type = Quantity(type=str, description='e.g., FORC, Hysteresis, IRM')
    start_time = Quantity(type=str)
    finish_time = Quantity(type=str)

    sample_setup = SubSection(section_def=MagnetometrySample)
    results = SubSection(section_def=MagnetometryResult, repeats=True)
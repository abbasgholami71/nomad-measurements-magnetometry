from typing import TYPE_CHECKING

import numpy as np
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNComponentEnum
from nomad.datamodel.metainfo.basesections import Measurement, MeasurementResult
from nomad.metainfo import Quantity, Section, SubSection

# Import external AGM reader
from readers_ientrance import read_micromag_agm

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad_measurements_magnetometry.schema_packages import m_package

# --- 1. Subsections ---


class AGMInstrument(ArchiveSection):
    configuration = Quantity(type=str)
    temperature_control = Quantity(type=str)
    hardware_version = Quantity(type=str)
    software_version = Quantity(type=str)
    units_of_measure = Quantity(type=str)
    temperature_in = Quantity(type=str)


class AGMSample(ArchiveSection):
    mass = Quantity(type=np.float64, description='g')
    volume = Quantity(type=np.float64, description='cm³')
    demagnetizing_factor = Quantity(type=np.float64)


class AGMSettings(ArchiveSection):
    field_range = Quantity(type=np.float64, description='Oe')
    field_command = Quantity(type=np.float64, description='Oe')
    moment_range = Quantity(type=np.float64, description='emu')
    averaging_time = Quantity(type=np.float64, unit='s')
    temperature_command = Quantity(type=np.float64)
    tmprtr_difference_correction = Quantity(type=str)
    orientation = Quantity(type=str)
    gradient = Quantity(type=np.float64)
    probe_factor = Quantity(type=np.float64)
    probe_q = Quantity(type=np.float64)
    probe_resonance = Quantity(type=np.float64, description='Hz')
    operating_frequency = Quantity(type=np.float64, description='Hz')
    sweep_mode = Quantity(type=str)


class AGMMeasurementDetails(ArchiveSection):
    description = Quantity(type=str)
    field_measured = Quantity(type=np.float64)
    temperature_measured = Quantity(type=np.float64)
    averages_completed = Quantity(type=np.float64)
    measured_on = Quantity(type=str)
    elapsed_time = Quantity(type=np.float64, unit='s')


class AGMProcessing(ArchiveSection):
    background_subtraction = Quantity(type=str)
    delta_m_processing = Quantity(type=str)
    demagnetizing_factor = Quantity(type=str)
    normalization = Quantity(type=str)
    normalization_factor = Quantity(type=np.float64)
    offset_field = Quantity(type=str)
    offset_moment = Quantity(type=str)
    pole_saturation = Quantity(type=str)
    slope_correction = Quantity(type=str)


class AGMViewport(ArchiveSection):
    left = Quantity(type=np.float64)
    right = Quantity(type=np.float64)
    bottom = Quantity(type=np.float64)
    top = Quantity(type=np.float64)
    show_x_axis = Quantity(type=str)
    show_y_axis = Quantity(type=str)


class AGMCharacterization(ArchiveSection):
    initial_slope = Quantity(type=np.float64)
    saturation = Quantity(type=np.float64)
    remanence = Quantity(type=np.float64)
    coercivity = Quantity(type=np.float64)
    s_star = Quantity(type=np.float64)


class AGMScriptSegment(ArchiveSection):
    segment_number = Quantity(type=int)
    averaging_time = Quantity(type=np.float64, unit='s')
    initial_field = Quantity(type=np.float64, description='Oe')
    field_increment = Quantity(type=np.float64, description='Oe')
    final_field = Quantity(type=np.float64, description='Oe')
    pause = Quantity(type=np.float64, unit='s')
    final_index = Quantity(type=int)


class AGMScript(ArchiveSection):
    number_of_segments = Quantity(type=int)
    number_of_data = Quantity(type=int)
    segments = SubSection(section_def=AGMScriptSegment, repeats=True)


class AGMResult(MeasurementResult):
    magnetic_field = Quantity(type=np.float64, shape=['*'], description='Oe')
    magnetic_moment = Quantity(type=np.float64, shape=['*'], description='emu')
    normalized_moment = Quantity(type=np.float64, shape=['*'])


# --- 2. Main Schema ---


class ELNAlternatingGradientMagnetometry(Measurement, EntryData):
    """
    Schema for MicroMag Alternating Gradient Magnetometry (AGM) data.
    """

    m_def = Section(
        a_eln=dict(lane_width='600px'),
        a_template=dict(measurement_identifiers=dict()),
    )

    data_file = Quantity(
        type=str,
        a_eln=dict(component=ELNComponentEnum.FileEditQuantity),
        a_browser=dict(adaptor='RawFileAdaptor'),
    )

    instrument_model = Quantity(type=str)
    data_format_version = Quantity(type=str)
    measurement_type = Quantity(type=str)
    measurement_mode = Quantity(type=str)

    instrument_setup = SubSection(section_def=AGMInstrument)
    sample_setup = SubSection(section_def=AGMSample)
    settings = SubSection(section_def=AGMSettings)
    measurement_details = SubSection(section_def=AGMMeasurementDetails)
    processing = SubSection(section_def=AGMProcessing)
    viewport = SubSection(section_def=AGMViewport)
    characterization = SubSection(section_def=AGMCharacterization)
    script = SubSection(section_def=AGMScript)
    results = SubSection(section_def=AGMResult, repeats=True)

    def _get_cleaners(self):
        def safe_float(val):
            if not val or val == 'N/A':
                return None
            try:
                return float(val)
            except ValueError:
                return None

        def safe_int(val):
            if not val or val == 'N/A':
                return None
            try:
                return int(val)
            except ValueError:
                return None

        return {'float': safe_float, 'int': safe_int}

    def _map_metadata(self, metadata: dict, cleaners: dict):
        safe_float = cleaners['float']
        safe_int = cleaners['int']

        if not self.instrument_setup:
            self.instrument_setup = AGMInstrument(
                configuration=metadata.get('Configuration'),
                temperature_control=metadata.get('Temperature control'),
                hardware_version=metadata.get('Hardware version'),
                software_version=metadata.get('Software version'),
                units_of_measure=metadata.get('Units of measure'),
                temperature_in=metadata.get('Temperature in'),
            )

        if not self.sample_setup:
            self.sample_setup = AGMSample(
                mass=safe_float(metadata.get('Mass')),
                volume=safe_float(metadata.get('Volume')),
                demagnetizing_factor=safe_float(metadata.get('Demagnetizing factor')),
            )

        if not self.settings:
            self.settings = AGMSettings(
                field_range=safe_float(metadata.get('Field range')),
                field_command=safe_float(metadata.get('Field (command)')),
                moment_range=safe_float(metadata.get('Moment range')),
                averaging_time=safe_float(metadata.get('Averaging time')),
                temperature_command=safe_float(metadata.get('Temperature (command)')),
                tmprtr_difference_correction=metadata.get(
                    'Tmprtr difference correction'
                ),
                orientation=metadata.get('Orientation'),
                gradient=safe_float(metadata.get('Gradient')),
                probe_factor=safe_float(metadata.get('Probe factor')),
                probe_q=safe_float(metadata.get('Probe Q')),
                probe_resonance=safe_float(metadata.get('Probe resonance')),
                operating_frequency=safe_float(metadata.get('Operating frequency')),
                sweep_mode=metadata.get('Sweep mode'),
            )

        if not self.measurement_details:
            self.measurement_details = AGMMeasurementDetails(
                description=metadata.get('Description', '').strip('"'),
                field_measured=safe_float(metadata.get('Field (measured)')),
                temperature_measured=safe_float(metadata.get('Temperature (measured)')),
                averages_completed=safe_float(metadata.get('Averages (completed)')),
                measured_on=metadata.get('Measured on'),
                elapsed_time=safe_float(metadata.get('Elapsed time')),
            )

        if not self.processing:
            self.processing = AGMProcessing(
                background_subtraction=metadata.get('Background subtraction'),
                delta_m_processing=metadata.get('Delta-m processing'),
                demagnetizing_factor=metadata.get('Demagnetizing factor'),
                normalization=metadata.get('Normalization'),
                normalization_factor=safe_float(metadata.get('Normalization factor')),
                offset_field=metadata.get('Offset (field)'),
                offset_moment=metadata.get('Offset (moment)'),
                pole_saturation=metadata.get('Pole saturation'),
                slope_correction=metadata.get('Slope correction'),
            )

        if not self.viewport:
            self.viewport = AGMViewport(
                left=safe_float(metadata.get('Left')),
                right=safe_float(metadata.get('Right')),
                bottom=safe_float(metadata.get('Bottom')),
                top=safe_float(metadata.get('Top')),
                show_x_axis=metadata.get('Show X-axis?'),
                show_y_axis=metadata.get('Show Y-axis?'),
            )

        if not self.characterization:
            self.characterization = AGMCharacterization(
                initial_slope=safe_float(metadata.get('Initial slope')),
                saturation=safe_float(metadata.get('Saturation')),
                remanence=safe_float(metadata.get('Remanence')),
                coercivity=safe_float(metadata.get('Coercivity')),
                s_star=safe_float(metadata.get('S*')),
            )

        if not self.script:
            self.script = AGMScript(
                number_of_segments=safe_int(metadata.get('Number of segments')),
                number_of_data=safe_int(metadata.get('Number of data')),
            )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        if not self.data_file:
            super().normalize(archive, logger)
            return

        try:
            with archive.m_context.raw_file(self.data_file) as file:
                agm_data = read_micromag_agm(file.name)

            cleaners = self._get_cleaners()
            metadata = agm_data.metadata

            self.instrument_model = metadata.get('Instrument Model')
            self.data_format_version = metadata.get('Data Format Version')
            self.measurement_type = metadata.get('Measurement Type')
            self.measurement_mode = metadata.get('Measurement Mode')
            self.time = metadata.get('Measured on')

            self._map_metadata(metadata, cleaners)

            if agm_data.segments is not None and not self.script.segments:
                seg_df = agm_data.segments
                segments_list = []
                for _, row in seg_df.iterrows():
                    seg = AGMScriptSegment(
                        segment_number=int(row['Segment Number']),
                        averaging_time=float(row['Averaging Time (s)']),
                        initial_field=float(row['Initial Field (Oe)']),
                        field_increment=float(row['Field Increment (Oe)']),
                        final_field=float(row['Final Field (Oe)']),
                        pause=float(row['Pause (s)']),
                        final_index=int(row['Final Index']),
                    )
                    segments_list.append(seg)
                self.script.segments = segments_list

            if not self.results:
                self.results = [AGMResult()]

            res = self.results[0]
            res.magnetic_field = agm_data.magnetic_field
            res.magnetic_moment = agm_data.magnetic_moment
            res.normalized_moment = agm_data.normalized_moment

        except Exception as e:
            if logger:
                logger.error(f'Error parsing AGM file: {e}')
            raise e

        super().normalize(archive, logger)


m_package.__init_metainfo__()

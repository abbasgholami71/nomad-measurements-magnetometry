from typing import TYPE_CHECKING

import numpy as np
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.metainfo.basesections import Measurement, MeasurementResult
from nomad.metainfo import Quantity, SchemaPackage, Section, SubSection
from readers_ientrance import read_lakeshore_vsm, read_micromag_agm

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = SchemaPackage()


# ==========================================
# 1. BASE MAGNETOMETRY
# ==========================================
class MagnetometrySample(ArchiveSection):
    sample_id = Quantity(type=str)
    mass = Quantity(type=np.float64, unit='g')
    volume = Quantity(type=np.float64, unit='cm**3')
    area = Quantity(type=np.float64, unit='cm**2')
    density = Quantity(type=np.float64, unit='g/cm**3')
    thickness = Quantity(type=np.float64, unit='mm')
    demagnetizing_factor = Quantity(
        type=np.float64, description='Generic or SI demagnetizing factor'
    )
    demagnetizing_factor_cgs = Quantity(
        type=np.float64, description='CGS demagnetizing factor'
    )


class MagnetometryResult(MeasurementResult):
    magnetic_field = Quantity(
        type=np.float64, shape=['*'], description='Applied magnetic field (Oe)'
    )
    magnetic_moment = Quantity(
        type=np.float64, shape=['*'], description='Measured magnetic moment (emu)'
    )
    normalized_moment = Quantity(
        type=np.float64, shape=['*'], description='Moment normalized by mass/volume'
    )
    time_stamp = Quantity(type=np.float64, shape=['*'], unit='s')
    step_array = Quantity(type=np.int32, shape=['*'])
    iteration_array = Quantity(type=np.int32, shape=['*'])
    segment_array = Quantity(type=np.int32, shape=['*'])
    field_status = Quantity(type=str, shape=['*'])
    moment_status = Quantity(type=str, shape=['*'])


class BaseMagnetometry(Measurement):
    instrument_model = Quantity(type=str)
    software_version = Quantity(type=str)
    measurement_type = Quantity(type=str)
    start_time = Quantity(type=str)
    finish_time = Quantity(type=str)

    sample_setup = SubSection(section_def=MagnetometrySample)
    results = SubSection(section_def=MagnetometryResult, repeats=True)


# ==========================================
# 2. AGM SCHEMA
# ==========================================
# --- 1. AGM-Specific Subsections ---


class AGMInstrument(ArchiveSection):
    configuration = Quantity(type=str)
    temperature_control = Quantity(type=str)
    hardware_version = Quantity(type=str)
    units_of_measure = Quantity(type=str)
    temperature_in = Quantity(type=str)


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
    description = Quantity(
        type=str, a_eln=dict(component=ELNComponentEnum.RichTextEditQuantity)
    )
    field_measured = Quantity(type=np.float64)
    temperature_measured = Quantity(type=np.float64)
    averages_completed = Quantity(type=np.float64)
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


# --- 2. Main AGM Schema ---


class ELNAlternatingGradientMagnetometry(BaseMagnetometry, EntryData):
    m_def = Section(label='MicroMag AGM', a_eln=dict(lane_width='600px'))

    data_file = Quantity(
        type=str,
        a_eln=dict(component=ELNComponentEnum.FileEditQuantity),
        a_browser=dict(adaptor='RawFileAdaptor'),
    )

    data_format_version = Quantity(type=str)
    measurement_mode = Quantity(type=str)

    instrument_setup = SubSection(section_def=AGMInstrument)
    settings = SubSection(section_def=AGMSettings)
    measurement_details = SubSection(section_def=AGMMeasurementDetails)
    processing = SubSection(section_def=AGMProcessing)
    viewport = SubSection(section_def=AGMViewport)
    characterization = SubSection(section_def=AGMCharacterization)
    script = SubSection(section_def=AGMScript)

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

    def _map_hardware_and_settings(self, metadata, safe_float):
        """Helper to map instrument, settings, and measurement details."""
        if not self.instrument_setup:
            self.instrument_setup = AGMInstrument(
                configuration=metadata.get('Configuration'),
                temperature_control=metadata.get('Temperature control'),
                hardware_version=metadata.get('Hardware version'),
                units_of_measure=metadata.get('Units of measure'),
                temperature_in=metadata.get('Temperature in'),
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
                elapsed_time=safe_float(metadata.get('Elapsed time')),
            )

    def _map_processing_and_script(self, metadata, agm_data, safe_float, safe_int):
        """Helper to map processing, viewport, characterization, and script segments."""
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

        # Map script segments DataFrame
        if agm_data.segments is not None and not self.script.segments:
            segments_list = []
            for _, row in agm_data.segments.iterrows():
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

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        if not self.data_file:
            super().normalize(archive, logger)
            return

        try:
            with archive.m_context.raw_file(self.data_file) as file:
                agm_data = read_micromag_agm(file.name)

            metadata = agm_data.metadata
            cleaners = self._get_cleaners()
            safe_float = cleaners['float']
            safe_int = cleaners['int']

            # Map BaseMagnetometry fields
            self.instrument_model = metadata.get('Instrument Model')
            self.software_version = metadata.get('Software version')
            self.measurement_type = metadata.get('Measurement Type')

            raw_time = metadata.get('Measured on')
            self.start_time = (
                str(raw_time).strip() if raw_time and raw_time != 'N/A' else None
            )

            # Map AGM Specific base fields
            self.data_format_version = metadata.get('Data Format Version')
            self.measurement_mode = metadata.get('Measurement Mode')

            # Map Base Sample
            if not self.sample_setup:
                self.sample_setup = MagnetometrySample(
                    mass=safe_float(metadata.get('Mass')),
                    volume=safe_float(metadata.get('Volume')),
                    demagnetizing_factor=safe_float(
                        metadata.get('Demagnetizing factor')
                    ),
                )

            # Map Subsections using helpers (Drastically reduces branch count!)
            self._map_hardware_and_settings(metadata, safe_float)
            self._map_processing_and_script(metadata, agm_data, safe_float, safe_int)

            # Results mapping
            if not self.results:
                self.results = [MagnetometryResult()]
            res = self.results[0]
            res.magnetic_field = agm_data.magnetic_field
            res.magnetic_moment = agm_data.magnetic_moment
            res.normalized_moment = agm_data.normalized_moment

        except Exception as e:
            if logger:
                logger.error(f'Error parsing AGM file: {e}')
            raise e

        super().normalize(archive, logger)


# ==========================================
# 3. VSM SCHEMA
# ==========================================


# --- 1. VSM-Specific Subsections ---
class FieldConfigurations(ArchiveSection):
    magnet_model = Quantity(type=str)
    power_supply = Quantity(type=str)
    magnet_mode = Quantity(type=str)
    head_amplitude = Quantity(type=str)
    gap_settings = Quantity(type=str)
    coil_set_name = Quantity(type=str)
    coil_set_serial_number = Quantity(type=str)
    coil_set_balance_number = Quantity(type=np.float64)
    moment_x_calibration_value = Quantity(type=np.float64, description='emu/volt')
    moment_x_calibration_field = Quantity(type=np.float64, description='Oe')
    moment_x_calibration_expected_moment = Quantity(type=np.float64, description='emu')
    moment_x_calibration_standard_id = Quantity(type=str)
    moment_x_calibration_comments = Quantity(type=str)


class AdvancedAcquisitionSetup(ArchiveSection):
    acquisition_mode = Quantity(type=str)
    pause_at_plus_minus_max_fields = Quantity(type=np.float64, unit='s')
    moment_meter_range_mode = Quantity(type=str)
    gaussmeter_range_mode = Quantity(type=str)
    gaussmeter_fixed_range = Quantity(type=str)


class AcquisitionSetup(ArchiveSection):
    saturation_field = Quantity(type=str)
    max_field = Quantity(type=str)
    forc_type = Quantity(type=str)
    max_hc_field = Quantity(type=np.float64, description='Oe')
    max_hu_field = Quantity(type=np.float64, description='Oe')
    min_hu_field = Quantity(type=np.float64, description='Oe')
    calibration_field_tolerance = Quantity(type=str)
    pause_at_calibration_field = Quantity(type=np.float64, unit='s')
    number_of_forcs = Quantity(type=np.int32)
    saturation_field_tolerance = Quantity(type=str)
    pause_at_saturation_field = Quantity(type=np.float64, unit='s')
    reversal_field_tolerance = Quantity(type=str)
    pause_at_reversal_fields = Quantity(type=np.float64, unit='s')
    enable_subtract_last_branches = Quantity(type=bool)
    last_branch_iterations = Quantity(type=np.int32)
    field_step_size = Quantity(type=np.float64, description='Oe')
    include_initial_curve = Quantity(type=bool)
    averaging_time = Quantity(type=np.float64, unit='s')
    show_forc_diagram_on_the_fly = Quantity(type=bool)
    smoothing_factor = Quantity(type=np.float64)
    rotate_45_degrees = Quantity(type=bool)
    truncate_for_a_rectangle_diagram = Quantity(type=bool)
    number_of_contours = Quantity(type=np.int32)
    correct_for_drift = Quantity(type=bool)
    advanced_acquisition_setup = SubSection(sub_section=AdvancedAcquisitionSetup)


class DisplaySetup(ArchiveSection):
    x_axis = Quantity(type=str)
    left_y_axis = Quantity(type=str)
    right_y_axis = Quantity(type=str)


# --- 2. Main VSM Schema ---


class ELNVibratingSampleMagnetometry(BaseMagnetometry, EntryData):
    m_def = Section(label='Lake Shore VSM')
    data_file = Quantity(
        type=str,
        a_eln=ELNAnnotation(component=ELNComponentEnum.FileEditQuantity),
    )

    field_configurations = SubSection(sub_section=FieldConfigurations)
    acquisition_setup = SubSection(sub_section=AcquisitionSetup)
    display_setup = SubSection(sub_section=DisplaySetup)

    def _get_cleaners(self, metadata):
        """Returns cleaning utilities for the mapping process."""

        def clean_float(key, strip_str=None):
            val = metadata.get(key)
            if val:
                if strip_str:
                    val = val.replace(strip_str, '')
                try:
                    return float(val.strip())
                except ValueError:
                    return None
            return None

        def clean_int(key):
            val = metadata.get(key)
            if val:
                try:
                    return int(val.strip())
                except ValueError:
                    return None
            return None

        def clean_bool(key):
            val = metadata.get(key, '').strip().lower()
            return val == 'true' if val in ['true', 'false'] else None

        return clean_float, clean_int, clean_bool

    def _map_acquisition_and_display(self, metadata, cleaners):
        """Maps acquisition and display setups."""
        cf, ci, cb = cleaners

        acq = AcquisitionSetup()
        acq.saturation_field = metadata.get('Saturation field')
        acq.max_field = metadata.get('Max field')
        acq.forc_type = metadata.get('FORC type')
        acq.max_hc_field = cf('Max Hc field', 'Oe')
        acq.max_hu_field = cf('Max Hu field', 'Oe')
        acq.min_hu_field = cf('Min Hu field', 'Oe')
        acq.calibration_field_tolerance = metadata.get('Calibration field tolerance')
        acq.pause_at_calibration_field = cf('Pause at calibration field', 's')
        acq.number_of_forcs = ci('Number of FORCs')
        acq.saturation_field_tolerance = metadata.get('Saturation field tolerance')
        acq.pause_at_saturation_field = cf('Pause at saturation field', 's')
        acq.reversal_field_tolerance = metadata.get('Reversal field tolerance')
        acq.pause_at_reversal_fields = cf('Pause at reversal fields', 's')
        acq.enable_subtract_last_branches = cb('Enable subtract Last branches')
        acq.last_branch_iterations = ci('Last branch iterations')
        acq.field_step_size = cf('Field_step size', 'Oe')
        acq.include_initial_curve = cb('Include initial curve')
        acq.averaging_time = cf('Averaging time', 's')
        acq.show_forc_diagram_on_the_fly = cb('Show FORC diagram on the fly')
        acq.smoothing_factor = cf('Smoothing factor')
        acq.rotate_45_degrees = cb('Rotate 45 degrees')
        acq.truncate_for_a_rectangle_diagram = cb('Truncate for a rectangle diagram')
        acq.number_of_contours = ci('Number of contours')
        acq.correct_for_drift = cb('Correct for drift')

        adv = AdvancedAcquisitionSetup()
        adv.acquisition_mode = metadata.get('Acquisition mode')
        adv.pause_at_plus_minus_max_fields = cf('Pause at +/- max fields', 's')
        adv.moment_meter_range_mode = metadata.get('Moment meter range mode')
        adv.gaussmeter_range_mode = metadata.get('Gaussmeter range mode')
        adv.gaussmeter_fixed_range = metadata.get('Gaussmeter fixed range')
        acq.advanced_acquisition_setup = adv
        self.acquisition_setup = acq

        ds = DisplaySetup()
        ds.x_axis = metadata.get('X axis')
        ds.left_y_axis = metadata.get('Left Y axis')
        ds.right_y_axis = metadata.get('Right Y axis')
        self.display_setup = ds

    def _map_sample_and_configs(self, metadata, cleaners):
        """Maps sample settings to base MagnetometrySample and VSM-specific field configs."""
        cf, _, _ = cleaners

        # Map VSM Specific configurations
        fc = FieldConfigurations()
        fc.magnet_model = metadata.get('Magnet')
        fc.power_supply = metadata.get('Power supply')
        fc.magnet_mode = metadata.get('Magnet mode')
        fc.head_amplitude = metadata.get('Head amplitude')
        fc.gap_settings = metadata.get('Gap settings')
        fc.coil_set_name = metadata.get('Coil set name')
        fc.coil_set_serial_number = metadata.get('Coil set serial number')
        fc.coil_set_balance_number = cf('Coil set balance number')
        fc.moment_x_calibration_value = cf('Moment X calibration value', 'emu/volt')
        fc.moment_x_calibration_field = cf('Moment X calibration field', 'Oe')
        fc.moment_x_calibration_expected_moment = cf(
            'Moment X calibration expected moment', 'emu'
        )
        fc.moment_x_calibration_standard_id = metadata.get(
            'Moment X calibration standard ID'
        )
        fc.moment_x_calibration_comments = metadata.get('Moment X calibration comments')
        self.field_configurations = fc

        # Map Sample to Base Schema
        if not self.sample_setup:
            self.sample_setup = MagnetometrySample()

        self.sample_setup.sample_id = metadata.get('ID')
        self.sample_setup.volume = cf('Volume', 'cm³')
        self.sample_setup.area = cf('Area', 'cm²')
        self.sample_setup.mass = cf('Mass', 'g')
        self.sample_setup.density = cf('Density', 'g/cm³')
        self.sample_setup.thickness = cf('Thickness', 'mm')
        self.sample_setup.demagnetizing_factor = cf('Demagnetization factor in SI')
        self.sample_setup.demagnetizing_factor_cgs = cf('Demagnetization factor in cgs')

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger'):
        if not self.data_file:
            super().normalize(archive, logger)
            return

        try:
            with archive.m_context.raw_file(self.data_file) as file:
                vsm_data = read_lakeshore_vsm(file.name)

            cleaners = self._get_cleaners(vsm_data.metadata)

            # Map to BaseMagnetometry fields
            self.instrument_model = 'Lake Shore VSM'
            self.software_version = vsm_data.metadata.get('Software Version')
            self.start_time = vsm_data.metadata.get('START TIME')
            self.finish_time = vsm_data.metadata.get('FINISH TIME')
            self.measurement_type = vsm_data.metadata.get('Measurement Type')

            # Map the subsections
            self._map_sample_and_configs(vsm_data.metadata, cleaners)
            self._map_acquisition_and_display(vsm_data.metadata, cleaners)

            # Map Results to Base Schema
            if not self.results:
                self.results = [MagnetometryResult()]

            res = self.results[0]
            res.step_array = vsm_data.step
            res.iteration_array = vsm_data.iteration
            res.segment_array = vsm_data.segment
            res.magnetic_field = vsm_data.magnetic_field
            res.magnetic_moment = vsm_data.magnetic_moment
            res.time_stamp = vsm_data.time_stamp
            res.field_status = vsm_data.field_status
            res.moment_status = vsm_data.moment_status

        except Exception as e:
            logger.error(f'Error parsing VSM file: {e}')

        super().normalize(archive, logger)


m_package.__init_metainfo__()

import json
from datetime import (
    datetime,
    timezone,
)
import argparse
from sqlalchemy import create_engine
import solution.database as database
from solution.enums import (
    UserType,
    Gender,
    ContactSystem,
    AppointmentStatus,
    DiagnosisStatus,
)
from solution.controllers import (
    UserObjectBuilder,
    AppointmentObjectBuilder,
    DiagnosisObjectBuilder,
)
import config


def _convert_iso_date_to_datetime(date_string):
    return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def _get_reference_object_id(reference_obj_dict):
    return reference_obj_dict.get('reference').split('/')[1]


def _create_user_object(db_session, user_type, obj_dict):
    user_obj_builder = UserObjectBuilder(
        db_session,
        user_type=user_type,
        object_id=obj_dict.get('id'),
    )

    # convert date string to date object
    if 'birthDate' in obj_dict:
        user_obj_builder.set_birth_date(datetime.strptime(obj_dict.get('birthDate'), '%Y-%m-%d').date())

    # convert gender string to Gender enum
    if 'gender' in obj_dict:
        user_obj_builder.set_gender(Gender[obj_dict.get('gender')])

    # set the active status (default to True if not specified in input)
    if 'active' in obj_dict:
        user_obj_builder.set_is_active(obj_dict.get('active'))
    else:
        user_obj_builder.set_is_active(True)

    # add/update user names
    user_obj_builder.clear_names()
    for name_obj_dict in obj_dict.get('name', []):
        user_obj_builder.add_name(
            family_name=name_obj_dict.get('family'),
            name_text=name_obj_dict.get('text'),
            given_names=name_obj_dict.get('given', []),
        )

    # add/update user contact info
    user_obj_builder.clear_contact_info()
    for contact_info_dict in obj_dict.get('contact', []):
        user_obj_builder.add_contact_info(
            system=ContactSystem[contact_info_dict.get('system')],
            name=contact_info_dict.get('use'),
            value=contact_info_dict.get('value'),
        )

    return user_obj_builder.object


def _create_appointment_object(db_session, obj_dict):
    # parse out actor and subject objects
    # assumption: the referenced objects exists in the DB
    doctor_id = _get_reference_object_id(obj_dict.get('actor', {}))
    patient_id = _get_reference_object_id(obj_dict.get('subject', {}))

    appt_obj_builder = AppointmentObjectBuilder(
        db_session,
        doctor_user_id=doctor_id,
        patient_user_id=patient_id,
        object_id=obj_dict.get('id'),
    )

    # convert period object into timestamp and duration
    period_obj_dict = obj_dict.get('period')
    start_dt = _convert_iso_date_to_datetime(period_obj_dict.get('start'))
    end_dt = _convert_iso_date_to_datetime(period_obj_dict.get('end'))

    start_time_ts = int(start_dt.timestamp())
    duration_secs = int((end_dt - start_dt).total_seconds())

    appt_obj_builder.set_appointment_time(
        start_time_ts=start_time_ts,
        duration_secs=duration_secs,
    )

    # add/update appointment reasons
    appt_obj_builder.clear_reasons()
    for reason_obj_dict in obj_dict.get('type', []):
        appt_obj_builder.add_reason(reason_obj_dict.get('text'))

    appt_obj_builder.set_status(AppointmentStatus[obj_dict.get('status')])

    return appt_obj_builder.object


def _create_diagnosis_object(db_session, obj_dict):

    # parse out the appointment object
    appt_id = _get_reference_object_id(obj_dict.get('appointment', {}))
    diagnosis_obj_builder = DiagnosisObjectBuilder(
        db_session,
        appointment_id=appt_id,
        object_id=obj_dict.get('id'),
    )

    # parse out the last updated timestamp
    last_updated_ts = _convert_iso_date_to_datetime(obj_dict.get('meta', {}).get('lastUpdated')).timestamp()
    diagnosis_obj_builder.set_last_updated_ts(
        ts=last_updated_ts
    )

    # add/update diagnosis details
    diagnosis_obj_builder.clear_details()
    for code_obj_dict in obj_dict.get('code', {}).get('coding', []):
        diagnosis_obj_builder.add_detail(
            code=code_obj_dict.get('code'),
            name=code_obj_dict.get('name'),
            system=code_obj_dict.get('system'),
        )

    diagnosis_obj_builder.set_status(DiagnosisStatus[obj_dict.get('status')])

    return diagnosis_obj_builder.object


def _import_appointment_summary(db_session, summary_dict):
    # by studying the "bundle" data, I see an appointment "bundle"
    # consists of four parts: 1) patient, 2) doctor, 3) appointment, 4) diagnosis
    # furthermore, I see appointment references patient and doctor, and diagnosis references appointment
    # meaning there is a strict order in creating the objects

    patient_obj_dict = None
    doctor_obj_dict = None
    appt_obj_dict = None
    diagnosis_obj_dict = None

    for entry in summary_dict.get('entry', []):
        obj_dict = entry.get('resource')
        if not obj_dict:
            print(f'unexpected resource entry: {obj_dict}')
            continue

        resource_type = obj_dict.get('resourceType').lower()
        if resource_type == 'patient':
            patient_obj_dict = obj_dict
        elif resource_type == 'doctor':
            doctor_obj_dict = obj_dict
        elif resource_type == 'appointment':
            appt_obj_dict = obj_dict
        elif resource_type == 'diagnosis':
            diagnosis_obj_dict = obj_dict
        else:
            print(f'unexpected resource type: {resource_type}')

    # create patient and doctor objects first
    _create_user_object(db_session, UserType.patient, patient_obj_dict)
    _create_user_object(db_session, UserType.doctor, doctor_obj_dict)

    # create appointment object (references patient and doctor objects)
    _create_appointment_object(db_session, appt_obj_dict)

    # create diagnosis object (references appointment object)
    _create_diagnosis_object(db_session, diagnosis_obj_dict)


def main():
    parser = argparse.ArgumentParser(description='Import Appointment Data - utility to import data related to a '
                                                 'medical appointment (in JSON format) into the system''s database.')
    parser.add_argument('json_file_path', help='path to the appointment summary data in JSON format.')

    args = vars(parser.parse_args())
    file_path = args.get('json_file_path')

    with open(file_path, 'r') as f:
        # todo: validate JSON schema validation in the future
        summary_dict = json.loads(f.read())

    # initialize database connection
    db_engine = create_engine(config.DATABASE_URL)

    # get DB Session factory and initialize DB schema if needed
    session_maker = database.get_session_maker(db_engine)

    with database.session_scope(session_maker) as db_session:
        _import_appointment_summary(db_session, summary_dict)
        print('data successfully imported!')


if __name__ == '__main__':
    main()

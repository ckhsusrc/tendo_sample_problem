import json
from sqlalchemy import create_engine
import solution.database as db
from solution.controllers import (
    PatientController,
    PostAppointmentSurveyObjectBuilder,
)
import config


def _conduct_patient_survey(db_session, appointment_summary):
    # conduct patient survey if we have not done so
    patient_first_name = 'Patient'
    for name_dict in appointment_summary.get('patient', {}).get('names', []):
        name = name_dict.get('first_name')
        if name:
            patient_first_name = name
            break

    doctor_last_name = 'Doctor'
    for name_dict in appointment_summary.get('doctor', {}).get('names', []):
        name = name_dict.get('last_name')
        if name:
            doctor_last_name = name
            break

    diagnosis_codes = appointment_summary.get('diagnosis', {}).get('codes', [])

    diagnosis_text = ''
    for i, code in enumerate(diagnosis_codes, 1):
        if i > 1:
            if i == len(diagnosis_codes):
                diagnosis_text += f', and {diagnosis_codes.get("name")}'
            else:
                diagnosis_text += f', {diagnosis_codes.get("name")}'
        else:
            diagnosis_text = code.get('name')

    survey_obj_builder = PostAppointmentSurveyObjectBuilder(
        db_session,
        appointment_id=appointment_summary.get('appointment', {}).get('id'),
    )

    while True:
        value = input(f'\nHi {patient_first_name}, on a scale of 1-10, would you recommend Dr {doctor_last_name} '
                      f'to a friend or family member?\n(1 = Would not recommend, 10 = Would strongly recommend)\n')
        try:
            value = int(value)
            if 1 <= value <= 10:
                survey_obj_builder.set_recommendation_rating(value)
                break
        except ValueError:
            # re-ask the question until input is valid
            pass

    value = input(
        f'\nThank you. You were diagnosed with "{diagnosis_text}".  Did Dr. {doctor_last_name} explain '
        f'how to manage this diagnosis in a way you could understand?\n')
    if value:
        yes_count = 0
        no_count = 0
        words = value.split()
        for word in words:
            lower_case_word = word.lower()
            if lower_case_word == 'yes':
                yes_count += 1
            elif lower_case_word == 'no':
                no_count += 1

        survey_obj_builder.set_diagnosis_feedback(value, yes_count > no_count)

    value = input(f'\nWe appreciate the feedback, one last question: how do you feel about '
                  f'being diagnosed with "{diagnosis_text}"?\n')
    if value:
        survey_obj_builder.set_patient_feeling(value)


def main():
    # initialize database connection
    db_engine = create_engine(config.DATABASE_URL)

    # get DB Session factory and initialize DB schema if needed
    session_maker = db.get_session_maker(db_engine)

    with db.session_scope(session_maker) as db_session:
        patient_controller = PatientController(db_session, config.PATIENT_ID)
        appt_summary = patient_controller.get_most_recent_appointment_summary()
        if not appt_summary.get('survey'):
            _conduct_patient_survey(db_session, appt_summary)
            appt_summary = patient_controller.get_most_recent_appointment_summary()

    print(f'\nThis is your survey response for your last appointment:\n'
          f'{json.dumps(appt_summary, sort_keys=True, indent=4, default=str)}')


if __name__ == '__main__':
    main()

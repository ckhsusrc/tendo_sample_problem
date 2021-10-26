import time
from solution.enums import (
    UserType,
)
import solution.models as models


class ObjectBuilderBase:
    def __init__(self, db_session, object_id=None):
        self._db_session = db_session
        self._object = None

    def _get_object_id(self):
        if self._object:
            return self._object.id
        else:
            return None

    @property
    def object(self):
        """
        primary key that uniquely identifies the object
        """
        return self._object

    @property
    def object_id(self):
        """
        primary key that uniquely identifies the object
        """
        return self._get_object_id()


class UserObjectBuilder(ObjectBuilderBase):
    def __init__(self, db_session, object_id=None):
        super().__init__(db_session, object_id)

        if object_id:
            self._object = db_session.query(models.User).filter_by(id=object_id).first()

        if not self._object:
            self._object = models.User(
                id=object_id,
            )
            db_session.add(self._object)
            db_session.flush()

    def set_user_type(self, user_type):
        self._object.user_type = user_type

    def set_is_active(self, is_active):
        self._object.is_active = is_active

    def set_birth_date(self, date):
        self._object.birth_date = date

    def set_gender(self, gender):
        self._object.gender = gender

    def clear_names(self):
        for name in self._db_session.query(models.UserName).filter_by(user_id=self._object.id):
            self._db_session.query(models.UserGivenName).filter_by(user_name_id=name.id).delete()
        self._db_session.query(models.UserName).filter_by(user_id=self._object.id).delete()
        self._db_session.flush()

    def add_name(self, family_name, name_text, given_names):
        user_name_obj = models.UserName(
            user_id=self._object.id,
            family_name=family_name,
            name_text=name_text,
        )
        self._db_session.add(user_name_obj)
        self._db_session.flush()

        for given_name in given_names:
            given_name_obj = models.UserGivenName(
                user_name_id=user_name_obj.id,
                given_name=given_name,
            )
            self._db_session.add(given_name_obj)
        self._db_session.flush()

    def clear_contact_info(self):
        self._db_session.query(models.UserContactInfo).filter_by(user_id=self._object.id).delete()
        self._db_session.flush()

    def add_contact_info(self, system, name, value):
        contact_info_obj = models.UserContactInfo(
            user_id=self._object.id,
            system=system,
            name=name,
            value=value,
        )
        self._db_session.add(contact_info_obj)
        self._db_session.flush()


class AppointmentObjectBuilder(ObjectBuilderBase):
    def __init__(self, db_session, object_id=None):
        super().__init__(db_session, object_id)

        if object_id:
            self._object = db_session.query(models.Appointment).filter_by(id=object_id).first()

        if not self._object:
            self._object = models.Appointment(
                id=object_id,
                start_time_ts=int(time.time()),
            )
            db_session.add(self._object)
            db_session.flush()

    def set_doctor_id(self, doctor_id):
        self._object.actor_id = doctor_id

    def set_patient_id(self, patient_id):
        self._object.subject_id = patient_id

    def set_appointment_time(self, start_time_ts, duration_secs):
        self._object.start_time_ts = start_time_ts
        self._object.duration_secs = duration_secs

    def set_status(self, status):
        self._object.status = status

    def clear_reasons(self):
        self._db_session.query(models.AppointmentReason).filter_by(appointment_id=self._object.id).delete()
        self._db_session.flush()

    def add_reason(self, reason_text):
        reason_obj = models.AppointmentReason(
            appointment_id=self._object.id,
            reason_text=reason_text
        )
        self._db_session.add(reason_obj)
        self._db_session.flush()


class DiagnosisObjectBuilder(ObjectBuilderBase):
    def __init__(self, db_session, object_id=None):
        super().__init__(db_session, object_id)

        if object_id:
            self._object = db_session.query(models.Diagnosis).filter_by(id=object_id).first()

        if not self._object:
            self._object = models.Diagnosis(
                id=object_id,
            )
            db_session.add(self._object)
            db_session.flush()

    def set_appointment_id(self, appointment_id):
        self._object.appointment_id = appointment_id

    def set_status(self, diagnosis_status):
        self._object.status = diagnosis_status

    def set_last_updated_ts(self, ts):
        self._object.last_updated_ts = ts

    def clear_details(self):
        self._db_session.query(models.DiagnosisDetail).filter_by(diagnosis_id=self._object.id).delete()
        self._db_session.flush()

    def add_detail(self, code, name, system):
        code_obj = self._db_session.query(models.DiagnosisCode).filter_by(code=code).first()
        if not code_obj:
            code_obj = models.DiagnosisCode(
                code=code,
                name=name,
                system=system,
            )
            self._db_session.add(code_obj)
            self._db_session.flush()

        detail_obj = models.DiagnosisDetail(
            diagnosis_id=self._object.id,
            diagnosis_code_id=code_obj.id,
        )
        self._db_session.add(detail_obj)
        self._db_session.flush()


class PostAppointmentSurveyObjectBuilder(ObjectBuilderBase):
    def __init__(self, db_session, object_id=None):
        super().__init__(db_session, object_id)

        if object_id:
            self._object = db_session.query(models.PostAppointmentSurvey).filter_by(id=object_id).first()

        if not self._object:
            self._object = models.PostAppointmentSurvey(
                id=object_id,
            )
            db_session.add(self._object)
            db_session.flush()

    def set_appointment_id(self, appointment_id):
        self._object.appointment_id = appointment_id

    def set_recommendation_rating(self, rating):
        self._object.recommendation_rating = rating

    def set_diagnosis_feedback(self, feedback_text, is_diagnosis_explained):
        self._object.diagnosis_feedback = feedback_text
        self._object.is_diagnosis_explained = is_diagnosis_explained

    def set_patient_feeling(self, feeling_text):
        self._object.patient_feeling = feeling_text


class PatientController:
    """
    A calls that represents a user (patient or doctor) in the Tendo SW system and
    supports patient related operations
    """

    def __init__(self, db_session, user_id):
        """
        :param object_id:  unique id/key that identifies the entity
        :param db_session: a connection to a database (concept is encapsulated as a "session" object in SqlAlchemy)
        """

        self._db_session = db_session
        self._user_id = user_id
        self._user = db_session.query(models.User).filter_by(id=self._user_id).one()

    def get_most_recent_appointment_summary(self):
        appt_obj = self._db_session.query(models.Appointment).filter_by(subject_id=self._user.id).order_by(
            models.Appointment.start_time_ts.desc()).limit(1).first()
        if not appt_obj:
            return None

        doctor_obj = self._db_session.query(models.User).filter_by(id=appt_obj.actor_id).first()
        diagnosis_obj = self._db_session.query(models.Diagnosis).filter_by(appointment_id=appt_obj.id).first()
        survey_obj = self._db_session.query(models.PostAppointmentSurvey).filter_by(appointment_id=appt_obj.id).first()

        return dict(
            appointment=appt_obj.to_dict(self._db_session),
            patient=self._user.to_dict(self._db_session),
            doctor=doctor_obj.to_dict(self._db_session) if doctor_obj else None,
            diagnosis=diagnosis_obj.to_dict(self._db_session) if diagnosis_obj else None,
            survey=survey_obj.to_dict(self._db_session) if survey_obj else None,
        )

import time
import uuid
from datetime import datetime
import sqlalchemy as sa
from solution.enums import (
    UserType,
    Gender,
    ContactSystem,
    AppointmentStatus,
    DiagnosisStatus,
)
from solution.database import Base


def timestamp_to_utc_datetime_str(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')


class DBObjectBase:
    def to_dict(self, db_session):
        return {c.key: getattr(self, c.key) for c in sa.inspect(self).mapper.column_attrs}


class User(Base, DBObjectBase):
    __tablename__ = 'User'

    # object id is an UUID, should consider using a datatype (UUID is a 16-byte data structure) for performance
    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid1()))

    user_type = sa.Column(sa.Enum(UserType), nullable=False, index=True, default=UserType.patient)
    is_active = sa.Column(sa.Boolean, nullable=False, default=True)
    birth_date = sa.Column(sa.Date, nullable=True)
    gender = sa.Column(sa.Enum(Gender), nullable=True, index=True)

    def to_dict(self, db_session):
        user_names = []
        for name_obj in db_session.query(UserName).filter_by(user_id=self.id):
            for given_name_obj in db_session.query(UserGivenName).filter_by(user_name_id=name_obj.id):
                user_names.append(dict(
                    last_name=name_obj.family_name,
                    first_name=given_name_obj.given_name,
                    name_text=name_obj.name_text,
                ))

        user_contacts = []
        for contact_info_obj in db_session.query(UserContactInfo).filter_by(user_id=self.id):
            user_contacts.append(dict(
                system=contact_info_obj.system,
                name=contact_info_obj.name,
                value=contact_info_obj.value,
            ))

        result = super().to_dict(db_session)
        result.update(dict(
            birth_date=self.birth_date.strftime('%Y-%m-%d') if self.birth_date else '',
            names=user_names,
            contact_info=user_contacts,
        ))

        return result


class UserName(Base, DBObjectBase):
    __tablename__ = 'UserName'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.String(36), sa.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    family_name = sa.Column(sa.String, nullable=True)
    name_text = sa.Column(sa.String, nullable=True)


class UserGivenName(Base, DBObjectBase):
    __tablename__ = 'UserGivenName'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_name_id = sa.Column(sa.Integer, sa.ForeignKey(UserName.id, ondelete='CASCADE'), nullable=False)
    given_name = sa.Column(sa.String, nullable=False)


class UserContactInfo(Base, DBObjectBase):
    __tablename__ = 'UserContactInfo'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    user_id = sa.Column(sa.String(36), sa.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    system = sa.Column(sa.Enum(ContactSystem), nullable=False, index=True)
    name = sa.Column(sa.String, nullable=False)
    value = sa.Column(sa.String, nullable=False)


class Appointment(Base, DBObjectBase):
    __tablename__ = 'Appointment'

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid1()))

    start_time_ts = sa.Column(sa.Integer, nullable=False)
    duration_secs = sa.Column(sa.Integer, nullable=False, default=1800)
    status = sa.Column(sa.Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.scheduled)
    actor_id = sa.Column(sa.String(36), sa.ForeignKey(User.id, ondelete='SET NULL'), nullable=True)
    subject_id = sa.Column(sa.String(36), sa.ForeignKey(User.id, ondelete='SET NULL'), nullable=True)

    def to_dict(self, db_session):
        reasons = []
        for reason_obj in db_session.query(AppointmentReason).filter_by(appointment_id=self.id):
            reasons.append(reason_obj.reason_text)

        result = super().to_dict(db_session)
        result.update(dict(
            start_time=timestamp_to_utc_datetime_str(self.start_time_ts),
            end_time=timestamp_to_utc_datetime_str(self.start_time_ts + self.duration_secs),
            reasons=reasons,
        ))

        return result


class AppointmentReason(Base, DBObjectBase):
    __tablename__ = 'AppointmentReason'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    appointment_id = sa.Column(sa.String(36), sa.ForeignKey(Appointment.id, ondelete='CASCADE'), nullable=False)
    reason_text = sa.Column(sa.Text, nullable=False)


class Diagnosis(Base, DBObjectBase):
    __tablename__ = 'Diagnosis'

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid1()))

    appointment_id = sa.Column(sa.String(36), sa.ForeignKey(Appointment.id, ondelete='SET NULL'), nullable=True)
    last_updated_ts = sa.Column(sa.Integer, nullable=False, default=lambda: int(time.time()))
    status = sa.Column(sa.Enum(DiagnosisStatus), nullable=False, default=DiagnosisStatus.thesis)

    def to_dict(self, db_session):
        db_session.flush()

        diagnosis_codes = []
        for detail_obj in db_session.query(DiagnosisDetail).filter_by(diagnosis_id=self.id):
            code_obj = db_session.query(DiagnosisCode).filter_by(id=detail_obj.diagnosis_code_id).first()
            if code_obj:
                diagnosis_codes.append(code_obj.to_dict(db_session))

        result = super().to_dict(db_session)
        result.update(dict(
            last_updated_time=timestamp_to_utc_datetime_str(self.last_updated_ts),
            codes=diagnosis_codes,
        ))

        return result


class DiagnosisCode(Base, DBObjectBase):
    __tablename__ = 'DiagnosisCode'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    code = sa.Column(sa.String, unique=True, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    system = sa.Column(sa.String, nullable=True)


class DiagnosisDetail(Base, DBObjectBase):
    __tablename__ = 'DiagnosisDetail'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    diagnosis_id = sa.Column(sa.String(36), sa.ForeignKey(Diagnosis.id, ondelete='CASCADE'), nullable=False)
    diagnosis_code_id = sa.Column(sa.Integer, sa.ForeignKey(DiagnosisCode.id, ondelete='CASCADE'), nullable=False)


class PostAppointmentSurvey(Base, DBObjectBase):
    __tablename__ = 'PostAppointmentSurvey'

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid1()))

    appointment_id = sa.Column(sa.String(36), sa.ForeignKey(Appointment.id, ondelete='SET NULL'), nullable=True)
    recommendation_rating = sa.Column(sa.Integer, nullable=False, default=5)
    is_diagnosis_explained = sa.Column(sa.Boolean, nullable=False, default=False)
    diagnosis_feedback = sa.Column(sa.Text, nullable=True)
    patient_feeling = sa.Column(sa.Text, nullable=True)

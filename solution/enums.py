import enum


class UserType(enum.Enum):
    doctor = 1
    patient = 2


class Gender(enum.Enum):
    female = 1
    male = 2


class ContactSystem(enum.Enum):
    phone = 1
    email = 2
    address = 3


class AppointmentStatus(enum.Enum):
    scheduled = 1
    in_progress = 2
    finished = 3
    missed = 4


class DiagnosisStatus(enum.Enum):
    thesis = 1
    verify = 2
    final = 3

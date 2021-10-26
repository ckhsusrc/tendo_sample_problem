import datetime
import json
import solution.database as db
from solution.enums import (
    UserType,
    Gender,
    ContactSystem,
)
from solution.controllers import (
    UserObjectBuilder,
)


def test_user_object_builder(db_session_maker):
    with db.session_scope(db_session_maker) as db_session:
        ev_user_type = UserType.patient
        ev_is_active = False
        ev_gender = Gender.male
        ev_birth_date = '1980-01-11'
        ev_family_name = 'Hsu'
        ev_name_text = 'CK Hsu'
        ev_given_names = ['CK', 'Chiakai']
        ev_contact_system = ContactSystem.email
        ev_contact_name = 'personal'
        ev_contact_value = 'ckhsusf@gmail.com'

        obj_builder = UserObjectBuilder(db_session, user_type=ev_user_type)
        obj_builder.set_is_active(ev_is_active)
        obj_builder.set_gender(ev_gender)
        obj_builder.set_birth_date(datetime.datetime.strptime(ev_birth_date, '%Y-%m-%d').date())
        obj_builder.add_name(family_name=ev_family_name, name_text=ev_name_text, given_names=ev_given_names)
        obj_builder.add_contact_info(system=ev_contact_system, name=ev_contact_name, value=ev_contact_value)

        test_obj_dict = obj_builder.object.to_dict(db_session)

        assert('id' in test_obj_dict)
        assert('user_type' in test_obj_dict)
        assert('is_active' in test_obj_dict)
        assert('gender' in test_obj_dict)
        assert('birth_date' in test_obj_dict)
        assert('names' in test_obj_dict)
        assert('contact_info' in test_obj_dict)

        assert(test_obj_dict['id'] is not None)
        assert(test_obj_dict['user_type'] == ev_user_type)
        assert(test_obj_dict['is_active'] == ev_is_active)
        assert(test_obj_dict['gender'] == Gender.male)
        assert(test_obj_dict['birth_date'] == ev_birth_date)
        assert(len(test_obj_dict['names']) == len(ev_given_names))
        assert(len(test_obj_dict['contact_info']) == 1)

    # start a new db_session and verify all the data have been saved to the DB and are properly recalled
    with db.session_scope(db_session_maker) as db_session:
        obj_builder = UserObjectBuilder(db_session, user_type=None, object_id=test_obj_dict.get('id'))
        recalled_obj_dict = obj_builder.object.to_dict(db_session)

    assert(json.dumps(test_obj_dict, default=str) == json.dumps(recalled_obj_dict, default=str))


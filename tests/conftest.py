import pytest
from sqlalchemy import create_engine
import solution.database as db


@pytest.fixture
def db_session_maker():
    yield db.get_session_maker(create_engine('sqlite:///:memory:', echo=True))

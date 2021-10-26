import sqlalchemy.orm as orm
from contextlib import contextmanager


Base = orm.declarative_base()


def get_session_maker(db_engine):
    """
    Initialize the Database by creating the DB Schema and returning a DB Session maker/factory
    :param db_engine: connection to the database server
    :return: a DB Session factory
    """
    result = orm.sessionmaker(bind=db_engine)
    Base.metadata.create_all(db_engine)

    return result


@contextmanager
def session_scope(session_maker):
    result = session_maker()
    try:
        yield result
        result.commit()
    except Exception:
        result.rollback()
        raise
    finally:
        result.close()

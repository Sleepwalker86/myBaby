import os
import tempfile

import pytest


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.environ['DATABASE_PATH'] = db_path

    from app import create_app
    flask_app = create_app()
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    yield flask_app

    os.close(db_fd)
    os.remove(db_path)
    os.environ.pop('DATABASE_PATH', None)


@pytest.fixture
def client(app):
    return app.test_client()

import os

import pytest


@pytest.fixture(scope="session")
def postgres_url():
    """
    Provides a PostgreSQL connection URL for integration tests.

    - When TEST_DATABASE_URL is set (e.g. running inside docker compose),
      uses that URL directly.
    - Otherwise spins up a fresh postgres container via testcontainers.
      This is the default when running tests on the host machine.
    """
    if url := os.environ.get("TEST_DATABASE_URL"):
        yield url
    else:
        from testcontainers.postgres import PostgresContainer

        with PostgresContainer("postgres:18-alpine") as pg:
            yield pg.get_connection_url().replace("psycopg2", "asyncpg")

import psycopg2
import pytest

from ingestion.config import pg_params


@pytest.fixture(scope="session")
def dwh():
    conn = psycopg2.connect(**pg_params("DWH"))
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def datahub():
    conn = psycopg2.connect(**pg_params("DATAHUB"))
    conn.autocommit = True
    yield conn
    conn.close()


def query(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def scalar(conn, sql, params=None):
    return query(conn, sql, params)[0][0]

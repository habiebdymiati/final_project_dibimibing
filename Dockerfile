# Image tunggal untuk Airflow + ingestion + dbt + pytest.
# dbt dipasang di virtualenv terpisah agar tidak bentrok dengan constraint Airflow.
FROM apache/airflow:2.9.3

USER airflow
COPY requirements.txt requirements-dbt.txt /tmp/

RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN python -m venv /home/airflow/dbt-venv \
 && /home/airflow/dbt-venv/bin/pip install --no-cache-dir -r /tmp/requirements-dbt.txt

# Pembungkus dbt: dbt, dbt-dwh (semua kecuali marts), dbt-datahub (hanya marts)
USER root
COPY --chmod=0755 scripts/dbt scripts/dbt-dwh scripts/dbt-datahub /usr/local/bin/
USER airflow

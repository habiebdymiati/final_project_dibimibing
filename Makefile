# Pintasan perintah. Semua berjalan di Docker.
RUN = docker compose run --rm runner

.PHONY: up down build ingest ingest-all flatten pipeline silver gold dashboard diagram granularitas sample-refresh test logs ps reset

up:            ## naikkan seluruh stack (db, MinIO, Airflow)
	docker compose up -d --build

down:          ## matikan stack (data tetap tersimpan di volume)
	docker compose down

reset:         ## matikan stack dan HAPUS semua data (volume)
	docker compose down -v

build:         ## build image pipeline
	docker compose build runner

ingest:        ## dua fase: API -> arsip MinIO -> raw (Postgres DWH); SOURCE=angkasabiruretail|angkasabiru
	$(RUN) python -m ingestion.run_ingest --source $(or $(SOURCE),angkasabiruretail)

ingest-all:    ## tarik seluruh sumber yang terdaftar di sources/*.yaml
	$(RUN) python -m ingestion.run_ingest --source angkasabiruretail
	$(RUN) python -m ingestion.run_ingest --source angkasabiru

flatten:       ## raw_<sumber> (JSONB) -> raw_table_<sumber> (truncate + insert); SOURCE=angkasabiruretail|angkasabiru
	$(RUN) python -m ingestion.flatten --source $(or $(SOURCE),angkasabiruretail)

pipeline:      ## extract + load + flatten satu sumber (sama dengan DAG Airflow); SOURCE=...
	$(RUN) python -m ingestion.run_ingest --source $(or $(SOURCE),angkasabiruretail)
	$(RUN) python -m ingestion.flatten --source $(or $(SOURCE),angkasabiruretail)

silver:        ## berkas referensi + dbt: raw_table_<sumber> -> staging -> silver (sumber yang sudah punya model staging)
	$(RUN) python -m ingestion.load_reference --source angkasabiru
	$(RUN) python -m ingestion.load_reference --source angkasabiruretail
	$(RUN) python -m ingestion.load_reference --source abdestination
	$(RUN) dbt build --target dwh

gold:          ## silver semua sumber -> star schema gold di Data Hub (setelah `make silver`)
	$(RUN) python -m ingestion.fdw_silver
	$(RUN) dbt build --target datahub

dashboard:     ## dashboard Metabase layer gold (idempoten; setelah `make gold`)
	$(RUN) python -m bi.setup_metabase

diagram:       ## diagram relasi tabel Angkasa Biru (raw_table, silver, alur) -> data_catalogue/resume/ (dari host)
	python3 scripts/catalogue/gen_diagram_relasi.py

granularitas:  ## bangun ulang lembar granularitas katalog efisien + inventaris raw_table (dari host)
	python3 scripts/catalogue/gen_granularitas.py

sample-refresh: ## segarkan data/sample/<sumber> dari snapshot raw terbaru; SOURCE=angkasabiruretail|angkasabiru
	$(RUN) python scripts/refresh_sample.py --source $(or $(SOURCE),angkasabiruretail)

test:          ## pytest (butuh `make up` dan data raw hasil `make pipeline`)
	$(RUN) pytest -v

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

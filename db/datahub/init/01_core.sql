-- Data Hub: tempat layer gold (star schema gabungan semua perusahaan). Tabel dibuat oleh dbt --target datahub.
--   fdw_silver_<sumber>  foreign table cermin silver_<sumber> di DWH; dibuat ingestion/fdw_silver.py
--   seed_gold            rujukan layer gold
--   staging_gold         tabel antara (metrik dan posisi pegawai)
--   gold                 dim_* dan fact_*
create schema if not exists seed_gold;
create schema if not exists staging_gold;
create schema if not exists gold;

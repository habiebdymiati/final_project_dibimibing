-- DWH. Tabel raw dibuat oleh pipeline ingestion; staging/seed/silver dibuat oleh dbt.
--   raw_<sumber>        payload JSONB per endpoint + _ingestion_log
--   raw_table_<sumber>  payload didatarkan (kunci -> kolom) oleh ingestion/flatten.py
--   Schema hasil transformasi berakhiran nama sumber, sama seperti raw_<sumber>; tabel/view di dalamnya juga.
--   reference_<sumber>  berkas referensi (CSV) sumber, mis. TMT karyawan; dimuat ingestion/load_reference.py
--   registry_<sumber>   registri kunci pegawai buatan DWH (id_employee), tidak pernah dinomori ulang
--   seed_<sumber>       tabel rujukan buatan DWH: ref_<nama>_<sumber>
--   staging_<sumber>    view aturan pemetaan raw_table_ -> struktur katalog: stg_<entitas>_<sumber>
--   silver_<sumber>     tabel per entitas katalog: <entitas>_<sumber> (mis. company_angkasabiru)
create schema if not exists raw_angkasabiruretail;
create schema if not exists raw_angkasabiru;
create schema if not exists raw_lms;
create schema if not exists raw_table_lms;
create schema if not exists raw_abdestination;
create schema if not exists raw_table_abdestination;
create schema if not exists reference_abdestination;
create schema if not exists registry_abdestination;
create schema if not exists seed_abdestination;
create schema if not exists raw_table_angkasabiruretail;
create schema if not exists raw_table_angkasabiru;
create schema if not exists reference_angkasabiru;
create schema if not exists reference_angkasabiruretail;
create schema if not exists registry_angkasabiru;
create schema if not exists seed_angkasabiru;
create schema if not exists staging_angkasabiru;
create schema if not exists silver_angkasabiru;

{# silver_angkasabiruretail.position_master_angkasabiruretail: data position_master milik Angkasa Biru Retail (aturan pemetaan di stg_position_master_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_master_angkasabiruretail') }}

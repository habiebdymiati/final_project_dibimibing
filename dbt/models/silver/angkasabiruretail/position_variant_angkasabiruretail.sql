{# silver_angkasabiruretail.position_variant_angkasabiruretail: data position_variant milik Angkasa Biru Retail (aturan pemetaan di stg_position_variant_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_variant_angkasabiruretail') }}

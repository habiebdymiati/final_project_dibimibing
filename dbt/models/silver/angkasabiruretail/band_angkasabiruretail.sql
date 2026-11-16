{# silver_angkasabiruretail.band_angkasabiruretail: data band milik Angkasa Biru Retail (aturan pemetaan di stg_band_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_band_angkasabiruretail') }}

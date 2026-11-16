{# silver.band_angkasabiru: data band milik Angkasa Biru (aturan pemetaan di stg_band_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_band_angkasabiru') }}

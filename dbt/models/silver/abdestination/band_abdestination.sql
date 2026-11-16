{# silver.band_abdestination: data band milik abdestination (aturan pemetaan di stg_band_abdestination). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_band_abdestination') }}

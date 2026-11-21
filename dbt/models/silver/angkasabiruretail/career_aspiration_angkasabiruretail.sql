{# silver.career_aspiration_angkasabiruretail: dari Angkasa Biru TMS (aturan pemetaan di stg_career_aspiration_angkasabiruretail). #}
{{ config(tags=['tms']) }}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_career_aspiration_angkasabiruretail') }}

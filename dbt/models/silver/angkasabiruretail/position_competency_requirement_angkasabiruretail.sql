{# silver_angkasabiruretail.position_competency_requirement_angkasabiruretail: data position_competency_requirement milik Angkasa Biru Retail (aturan pemetaan di stg_position_competency_requirement_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_competency_requirement_angkasabiruretail') }}

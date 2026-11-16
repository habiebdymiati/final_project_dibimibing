{# silver.position_competency_requirement_angkasabiru: data position_competency_requirement milik Angkasa Biru (aturan pemetaan di stg_position_competency_requirement_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_competency_requirement_angkasabiru') }}

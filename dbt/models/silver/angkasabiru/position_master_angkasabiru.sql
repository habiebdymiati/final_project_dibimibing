{# silver.position_master_angkasabiru: data position_master milik Angkasa Biru (aturan pemetaan di stg_position_master_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_master_angkasabiru') }}

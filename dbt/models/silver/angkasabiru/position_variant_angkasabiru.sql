{# silver.position_variant_angkasabiru: data position_variant milik Angkasa Biru (aturan pemetaan di stg_position_variant_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_position_variant_angkasabiru') }}

{# silver.org_unit_angkasabiru: data org_unit milik Angkasa Biru (aturan pemetaan di stg_org_unit_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_org_unit_angkasabiru') }}

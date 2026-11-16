{# silver.company_angkasabiru: data company milik Angkasa Biru (aturan pemetaan di stg_company_angkasabiru). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_company_angkasabiru') }}

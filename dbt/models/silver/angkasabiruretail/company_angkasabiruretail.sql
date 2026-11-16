{# silver_angkasabiruretail.company_angkasabiruretail: data company milik Angkasa Biru Retail (aturan pemetaan di stg_company_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_company_angkasabiruretail') }}

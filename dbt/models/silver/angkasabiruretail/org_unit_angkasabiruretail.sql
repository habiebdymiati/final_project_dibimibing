{# silver_angkasabiruretail.org_unit_angkasabiruretail: data org_unit milik Angkasa Biru Retail (aturan pemetaan di stg_org_unit_angkasabiruretail). #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_org_unit_angkasabiruretail') }}

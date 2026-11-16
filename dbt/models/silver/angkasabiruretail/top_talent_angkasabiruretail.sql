{# silver_angkasabiruretail.top_talent_angkasabiruretail: penanda top talent dari master data (aturan di stg_top_talent_angkasabiruretail). Bukan entitas katalog. #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_top_talent_angkasabiruretail') }}

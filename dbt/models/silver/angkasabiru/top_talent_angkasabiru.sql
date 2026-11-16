{# silver_angkasabiru.top_talent_angkasabiru: penanda top talent dari master data (aturan di stg_top_talent_angkasabiru). Bukan entitas katalog. #}
select *, current_timestamp as dwh_loaded_at from {{ ref('stg_top_talent_angkasabiru') }}

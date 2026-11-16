{#
  REGISTRI id_employee Angkasa Biru Destinasi (kunci pegawai buatan DWH).
  Bentuk : VARCHAR berisi 8 digit = 30 + enam digit nomor urut -> '30000001', '30000002', ...
           Awalan 30 membedakan dari Angkasa Biru (10) dan Angkasa Biru Retail (20).
  Urutan : tahun/tanggal masuk (TMT) paling awal mendapat nomor terkecil; TMT sama diurutkan menurut NIP;
           NIP tanpa TMT di belakang. ID HARUS STABIL: incremental, hanya menambah NIP baru.
#}
{{ config(
    materialized='incremental',
    unique_key=['source_system', 'nip'],
    full_refresh=false,
    on_schema_change='fail',
    post_hook=[
        "create unique index if not exists uq_registry_id_employee_abdestination_nip on {{ this }} (source_system, nip)",
        "create unique index if not exists uq_registry_id_employee_abdestination_id on {{ this }} (id_employee)"
    ]
) }}

with semesta as (
    select source_system, nip, dt_tmt from {{ ref('int_nip_pegawai_abdestination') }}
),
baru as (
    select s.* from semesta s
    {% if is_incremental() %}
    where not exists (select 1 from {{ this }} t where t.source_system = s.source_system and t.nip = s.nip)
    {% endif %}
),
terakhir as (
    select {% if is_incremental() %}coalesce((select max(urutan) from {{ this }}), 0){% else %}0{% endif %} as n
)
select
    b.source_system, b.nip, b.dt_tmt,
    cast(t.n + row_number() over (order by b.dt_tmt nulls last, b.source_system, b.nip) as integer)            as urutan,
    cast(30000000 + t.n + row_number() over (order by b.dt_tmt nulls last, b.source_system, b.nip) as varchar) as id_employee,
    current_timestamp as dwh_assigned_at
from baru b
cross join terakhir t

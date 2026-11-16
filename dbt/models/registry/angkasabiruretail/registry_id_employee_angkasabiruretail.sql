{#
  REGISTRI id_employee Angkasa Biru Retail (kunci pegawai buatan DWH).

  Bentuk : VARCHAR berisi 8 digit = 20 + enam digit nomor urut -> '20000001', '20000002', ... (keputusan 07 Nov 2026).
           Awalan 20 membedakan Angkasa Biru Retail dari Angkasa Biru (awalan 10), jadi ID tidak bentrok.
  Kunci  : NIP lama (old_nip), karena itulah nomor yang dikenal semua endpoint Angkasa Biru Retail.
  Urutan : tanggal mulai bekerja paling awal mendapat nomor terkecil; tanggal sama diurutkan menurut NIP.
           NIP tanpa tanggal mulai bekerja diberi nomor sesudahnya.

  ID HARUS STABIL: model incremental, hanya MENAMBAH NIP yang belum terdaftar dan melanjutkan nomor terakhir
  (dihitung dari kolom `urutan`). full_refresh dimatikan supaya ID tidak pernah dinomori ulang.
#}
{{ config(
    materialized='incremental',
    unique_key=['source_system', 'nip'],
    full_refresh=false,
    on_schema_change='fail',
    post_hook=[
        "create unique index if not exists uq_registry_id_employee_angkasabiruretail_nip on {{ this }} (source_system, nip)",
        "create unique index if not exists uq_registry_id_employee_angkasabiruretail_id on {{ this }} (id_employee)"
    ]
) }}

with semesta as (
    select source_system, nip, dt_tmt from {{ ref('int_nip_pegawai_angkasabiruretail') }}
),
baru as (
    select s.*
    from semesta s
    {% if is_incremental() %}
    where not exists (select 1 from {{ this }} t where t.source_system = s.source_system and t.nip = s.nip)
    {% endif %}
),
terakhir as (
    select {% if is_incremental() %}coalesce((select max(urutan) from {{ this }}), 0){% else %}0{% endif %} as n
)
select
    b.source_system,
    b.nip,
    b.dt_tmt,
    cast(t.n + row_number() over (order by b.dt_tmt nulls last, b.source_system, b.nip) as integer)              as urutan,
    cast(20000000 + t.n + row_number() over (order by b.dt_tmt nulls last, b.source_system, b.nip) as varchar)   as id_employee,
    current_timestamp as dwh_assigned_at
from baru b
cross join terakhir t

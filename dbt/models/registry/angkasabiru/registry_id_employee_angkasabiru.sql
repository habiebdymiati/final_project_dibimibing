{#
  REGISTRI id_employee Angkasa Biru (kunci pegawai buatan DWH).

  Bentuk : VARCHAR berisi 8 digit = 10 + enam digit nomor urut -> '10000001', '10000002', ... (keputusan 07 Nov 2026).
           Awalan 10 membedakan Angkasa Biru dari Angkasa Biru Retail (awalan 20). Nomor berikutnya SELALU dihitung dari kolom
           `urutan` (integer), bukan dari max(id_employee), karena urutan teks tidak sama dengan urutan angka.
           PERHATIAN: bentuknya sama dengan sebagian old_nip (2000xxxx), jadi jangan pernah menggabungkan id_employee
           dengan old_nip; keduanya kolom berbeda dan sama-sama bisa berisi angka yang sama untuk pegawai berbeda.
  Urutan : TMT karyawan paling awal mendapat nomor terkecil; TMT sama diurutkan menurut NIP.
           NIP yang tidak ada di berkas referensi TMT diberi nomor sesudah yang ber-TMT.

  ID HARUS STABIL: sekali diberikan tidak pernah berubah. Karena itu model ini incremental dan hanya
  MENAMBAH NIP yang belum terdaftar (melanjutkan nomor terakhir); pegawai baru tidak menggeser nomor lama.
  full_refresh dimatikan supaya `dbt build --full-refresh` tidak menomori ulang seluruh pegawai.
#}
{{ config(
    materialized='incremental',
    unique_key=['source_system', 'nip'],
    full_refresh=false,
    on_schema_change='fail',
    post_hook=[
        "create unique index if not exists uq_registry_id_employee_angkasabiru_nip on {{ this }} (source_system, nip)",
        "create unique index if not exists uq_registry_id_employee_angkasabiru_id on {{ this }} (id_employee)"
    ]
) }}

with semesta as (
    select source_system, nip, dt_tmt from {{ ref('int_nip_pegawai_angkasabiru') }}
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
    cast(10000000 + t.n + row_number() over (order by b.dt_tmt nulls last, b.source_system, b.nip) as varchar) as id_employee,
    current_timestamp as dwh_assigned_at
from baru b
cross join terakhir t

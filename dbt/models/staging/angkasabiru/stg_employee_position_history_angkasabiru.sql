{#
  Mapping AB: employee_position_history <- employee_position_history (nama kolom sama dengan target).
  dt_position_end belum dikirim API -> NULL. job_class: hanya angka (tanda "-" -> NULL).
  fk_position_variant_id, org_unit_name: nilai API; bila kosong, HANYA baris riwayat terakhir diisi dari nominatif
  (aturannya di int_posisi_terkini_angkasabiru). Baris lama tetap apa adanya karena nominatif hanya menggambarkan satu waktu.
#}
select
    {{ ab('employee_position_history', 'id_position_history') }}    as id_position_history,
    cast({{ ab('employee_position_history', 'new_nip') }} as varchar) as new_nip,
    coalesce({{ ab('employee_position_history', 'fk_position_variant_id') }},
             case when t.id_riwayat_terakhir = {{ ab('employee_position_history', 'id_position_history') }}
                  then t.fk_position_variant_id_nominatif end) as fk_position_variant_id,
    {{ ab('employee_position_history', 'position_name') }}          as position_name,
    {{ ab('employee_position_history', 'position_type') }}          as position_type,
    {{ ke_int(ab('employee_position_history', 'job_class')) }}      as job_class,
    coalesce({{ ab('employee_position_history', 'org_unit_name') }},
             case when t.id_riwayat_terakhir = {{ ab('employee_position_history', 'id_position_history') }}
                  then t.org_unit_name_nominatif end) as org_unit_name,
    {{ baku('angkasabiru', 'company_name', ab('employee_position_history', 'company_name')) }} as company_name,
    {{ ke_tanggal(ab('employee_position_history', 'dt_position_start')) }} as dt_position_start,
    {{ ke_tanggal(ab('employee_position_history', 'dt_position_end')) }}   as dt_position_end,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_position_history') }} r
left join {{ ref('int_posisi_terkini_angkasabiru') }} t
       on t.new_nip = {{ ab('employee_position_history', 'new_nip') }}
where {{ ab('employee_position_history', 'id_position_history') }} is not null

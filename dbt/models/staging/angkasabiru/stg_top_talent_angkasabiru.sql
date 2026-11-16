{#
  Penanda top talent Angkasa Biru dari kolom "Top Talent" pada master data (keputusan 07 November 2026). Di luar Mapping Field API.
    new_nip       : NIK di master data = new_nip.
    is_top_talent : 'Ya' -> true; 'Tidak' atau kosong -> false. NIK yang muncul lebih dari sekali: true bila ada yang 'Ya'.
  Hanya NIK yang dikenal registri id_employee yang diambil. Berkas referensinya sudah dibatasi pada baris perusahaan ini dan
  kolom NIK + Top Talent (blok reference_files di sources/angkasabiru.yaml).
#}
with master as (
    select nullif(btrim(m.nik), '') as nip, m.top_talent, m._file, m._loaded_at
    from {{ source('ref_ab', 'master_data_angkasabiru') }} m
),
per_nip as (
    select
        nip,
        coalesce(bool_or(lower(btrim(top_talent)) = 'ya'), false) as is_top_talent,
        max(_file)      as dwh_batch_id,
        max(_loaded_at) as dwh_extracted_at
    from master
    where nip is not null
    group by nip
),
berid as (
    select
        {{ id_employee('angkasabiru', 'p.nip') }} as id_employee,
        cast(p.nip as varchar)   as new_nip,
        p.is_top_talent,
        cast('angkasabiru' as text) as dwh_source_system,
        p.dwh_batch_id,
        p.dwh_extracted_at
    from per_nip p
)
select * from berid where id_employee is not null

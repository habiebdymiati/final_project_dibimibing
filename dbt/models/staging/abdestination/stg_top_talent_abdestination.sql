{#
  Penanda top talent Angkasa Biru Destinasi dari kolom "Top Talent" master data (saring Kode Perusahaan ABD).
#}
with master as (
    select nullif(btrim(m.nik), '') as nip, m.top_talent, m._file, m._loaded_at
    from {{ source('ref_abd', 'master_data_abdestination') }} m
),
per_nip as (
    select nip,
           coalesce(bool_or(lower(btrim(top_talent)) = 'ya'), false) as is_top_talent,
           max(_file) as dwh_batch_id, max(_loaded_at) as dwh_extracted_at
    from master
    where nip is not null
    group by nip
),
berid as (
    select
        {{ id_employee('abdestination', 'p.nip') }} as id_employee,
        cast(p.nip as varchar) as new_nip,
        p.is_top_talent,
        cast('abdestination' as text) as dwh_source_system,
        p.dwh_batch_id, p.dwh_extracted_at
    from per_nip p
)
select * from berid where id_employee is not null

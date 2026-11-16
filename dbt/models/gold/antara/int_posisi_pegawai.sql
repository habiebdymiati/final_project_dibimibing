{#
  Posisi tiap pegawai menurut riwayat posisi silver, satu baris per (sumber, new_nip).
    dt_mulai_posisi     : tanggal mulai baris riwayat TERAKHIR.
    id_position_master  : baris riwayat terakhir yang kodenya ADA di position_master. Kode riwayat kedua sumber memakai kode
                          posisi yang sama dengan id_position_master dan id_position_variant.
    dt_mulai_job_family : tanggal mulai paling awal di antara baris riwayat yang job family-nya sama dengan job family
                          terkini (dasar komponen EQS Pengalaman: tenure dalam job family yang sama).
  Dipakai dim_employee (posisi dan job family terkini), int_employee_metrics, dan fact_talent_analytics.
#}
with riwayat as (
    {{ dari_silver('employee_position_history', 'new_nip, fk_position_variant_id as fk, dt_position_start, id_position_history') }}
),
master as (
    {{ dari_silver('position_master', 'id_position_master, id_job_family') }}
),
baris as (
    select r.source_system_code, r.new_nip, r.dt_position_start,
           case when r.id_position_history ~ '^[0-9]+$' then r.id_position_history::bigint end as urut,
           m.id_position_master, m.id_job_family
    from riwayat r
    left join master m on m.source_system_code = r.source_system_code and m.id_position_master = r.fk
    where r.new_nip is not null
),
terkini as (
    select distinct on (source_system_code, new_nip) source_system_code, new_nip, dt_position_start as dt_mulai_posisi
    from baris
    order by source_system_code, new_nip, dt_position_start desc nulls last, urut desc nulls last
),
terkini_master as (
    select distinct on (source_system_code, new_nip) source_system_code, new_nip, id_position_master, id_job_family
    from baris
    where id_position_master is not null
    order by source_system_code, new_nip, dt_position_start desc nulls last, urut desc nulls last
),
keluarga as (
    select b.source_system_code, b.new_nip, min(b.dt_position_start) as dt_mulai_job_family
    from baris b
    join terkini_master m on m.source_system_code = b.source_system_code and m.new_nip = b.new_nip
                         and m.id_job_family = b.id_job_family
    group by 1, 2
)
select
    t.source_system_code,
    t.new_nip,
    t.dt_mulai_posisi,
    m.id_position_master,
    m.id_job_family,
    f.dt_mulai_job_family
from terkini t
left join terkini_master m on m.source_system_code = t.source_system_code and m.new_nip = t.new_nip
left join keluarga f on f.source_system_code = t.source_system_code and f.new_nip = t.new_nip

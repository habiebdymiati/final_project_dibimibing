{#
  Satu baris per pegawai di semua perusahaan, termasuk yang tidak aktif. employee_key = id_employee buatan DWH (unik lintas
  perusahaan karena awalannya berbeda); employee_id = NIP milik sumber. Atribut mengikuti katalog: tanpa kontak dan identitas administratif.
#}
with emp as (
    {{ dari_silver('employee_profile', 'id_employee, new_nip, full_name, band_name, area_name, directorate_name, org_group_name') }}
),
identitas as (
    {{ dari_silver('employee_identification', 'id_employee, gender, dt_birth, job_class') }}
),
family as (
    {{ dari_silver('job_family', 'id_job_family, job_family_name') }}
)
select
    e.id_employee as employee_key,
    e.new_nip as employee_id,
    e.full_name,
    i.gender,
    case when i.dt_birth is not null then extract(year from age({{ as_of() }}, i.dt_birth))::int end as age,
    i.job_class as current_grade,
    e.band_name as current_band,
    f.job_family_name as current_job_family,
    e.area_name as current_area,
    e.directorate_name as current_directorate,
    e.org_group_name as current_org_group
from emp e
left join identitas i on i.id_employee = e.id_employee
left join {{ ref('int_posisi_pegawai') }} p on p.source_system_code = e.source_system_code and p.new_nip = e.new_nip
left join family f on f.source_system_code = e.source_system_code and f.id_job_family = p.id_job_family

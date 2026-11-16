{#
  Metrik per pegawai (termasuk yang tidak aktif) pada tanggal acuan; dipakai fact_employee_snapshot.
  is_top_talent dari silver top_talent_<sumber> (kolom Top Talent master data); pegawai di luar daftar = false.
  contract_type_key: kontrak aktif terbaru; bila tidak ada kontrak (Angkasa Biru) memakai employment_type yang sudah diseragamkan.
#}
with emp as (
    {{ dari_silver('employee_profile', 'id_employee, new_nip, employment_status') }}
),
identitas as (
    {{ dari_silver('employee_identification', 'id_employee, dt_start_work, dt_grade_start, employment_type') }}
),
perusahaan as (
    select source_system_code, min(id_company) as id_company from ({{ dari_silver('company', 'id_company') }}) c group by 1
),
kontrak as (
    select distinct on (id_employee) id_employee, contract_type, dt_contract_end, contract_status
    from ({{ dari_silver('employee_contract', 'id_employee, contract_type, dt_contract_start, dt_contract_end, contract_status') }}) k
    order by id_employee, (contract_status = 'aktif') desc nulls last, dt_contract_start desc nulls last
),
kinerja as (
    select id_employee, avg(performance_score) as skor
    from ({{ dari_silver('employee_performance_history', 'id_employee, period_year, performance_score') }}) p
    where period_year > extract(year from {{ as_of() }}) - {{ var('performance_window_years') }}
      and period_year <= extract(year from {{ as_of() }})
    group by 1
),
talent as (
    select id_employee, is_top_talent
    from ({{ dari_silver('top_talent', 'id_employee, is_top_talent') }}) tt
),
jobfit as (
    -- job fit periode terbaru per pegawai (katalog BRD 4.5; komponen EQS Kompetensi)
    select distinct on (id_employee) id_employee, job_fit_score
    from ({{ dari_silver('competency_assessment', 'id_employee, job_fit_score, dt_assessment') }}) a
    where job_fit_score is not null
    order by id_employee, dt_assessment desc nulls last
),
agility as (
    -- learning agility periode terbaru per pegawai (katalog BRD 4.4; sumbu capacity 9-Box)
    select distinct on (id_employee) id_employee, learning_agility_score
    from ({{ dari_silver('learning_agility_assessment', 'id_employee, learning_agility_score, dt_assessment') }}) a
    where learning_agility_score is not null
    order by id_employee, dt_assessment desc nulls last
),
pelatihan as (
    -- completion rate pelatihan wajib/penjenjangan (katalog BRD 4.3; komponen EQS Pelatihan)
    select id_employee,
           count(*) filter (where dt_completion is not null)::numeric / count(*) as mandatory_completion_rate
    from ({{ dari_silver('learning_history', 'id_employee, is_mandatory, dt_completion') }}) l
    where is_mandatory
    group by 1
),
disiplin_baris as (
    {{ dari_silver('employee_disciplinary', 'id_employee, is_aktif, dt_disciplinary, dt_disciplinary_end') }}
),
disiplin as (
    select id_employee,
           bool_or(coalesce(is_aktif,
                   dt_disciplinary >= {{ as_of() }} - make_interval(months => {{ var('disciplinary_active_months') }})
                   and (dt_disciplinary_end is null or dt_disciplinary_end >= {{ as_of() }}))) as ada_aktif
    from disiplin_baris
    group by 1
),
sumber_disiplin as (
    select distinct source_system_code from disiplin_baris
)
select
    e.source_system_code,
    e.kode_sumber,
    e.id_employee,
    e.new_nip,
    e.employment_status,
    coalesce(c.id_company, 'UNKNOWN') as company_key,
    coalesce(v.position_variant_key, 'UNKNOWN') as position_variant_key,
    coalesce(v.org_unit_key, 'UNKNOWN') as org_unit_key,
    coalesce(k.contract_type, i.employment_type, 'UNKNOWN') as contract_type_key,
    case when k.contract_status = 'aktif' then k.dt_contract_end end as contract_expiry_date,
    {{ months_between('p.dt_mulai_posisi', as_of()) }} as tenure_in_position_months,
    {{ months_between('i.dt_grade_start', as_of()) }} as tenure_in_grade_months,
    {{ months_between('i.dt_start_work', as_of()) }} as tenure_in_company_months,
    round(n.skor, 2) as performance_score_avg_3y,
    jf.job_fit_score,
    ag.learning_agility_score,
    {{ months_between('p.dt_mulai_job_family', as_of()) }} as tenure_in_job_family_months,
    round(pl.mandatory_completion_rate * 100, 1) as pct_mandatory_training,
    coalesce(pl.mandatory_completion_rate >= 1, false) as is_mandatory_training_complete,
    coalesce(tt.is_top_talent, false) as is_top_talent,
    coalesce(d.ada_aktif, false) as has_active_disciplinary,
    sd.source_system_code is not null as ada_data_disiplin
from emp e
left join identitas i on i.id_employee = e.id_employee
left join perusahaan c on c.source_system_code = e.source_system_code
left join {{ ref('int_posisi_pegawai') }} p on p.source_system_code = e.source_system_code and p.new_nip = e.new_nip
left join {{ ref('dim_position_variant') }} v on v.position_variant_key = e.kode_sumber || '-' || p.id_position_master
left join kontrak k on k.id_employee = e.id_employee
left join kinerja n on n.id_employee = e.id_employee
left join talent tt on tt.id_employee = e.id_employee
left join jobfit jf on jf.id_employee = e.id_employee
left join agility ag on ag.id_employee = e.id_employee
left join pelatihan pl on pl.id_employee = e.id_employee
left join disiplin d on d.id_employee = e.id_employee
left join sumber_disiplin sd on sd.source_system_code = e.source_system_code

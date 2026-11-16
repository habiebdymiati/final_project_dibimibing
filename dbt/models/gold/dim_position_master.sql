{# Master posisi semua perusahaan; job family, job function, dan nama tipe posisi diambil dari rujukan masing-masing perusahaan. #}
with master as (
    {{ dari_silver('position_master', 'id_position_master, position_master_name, fk_position_type_id, id_job_family, id_job_function') }}
),
family as (
    {{ dari_silver('job_family', 'id_job_family, job_family_name') }}
),
fungsi as (
    {{ dari_silver('job_function', 'id_job_function, job_function_name') }}
)
select
    m.kode_sumber || '-' || m.id_position_master as position_master_key,
    m.id_position_master as position_master_id,
    m.position_master_name,
    f.job_family_name,
    g.job_function_name,
    t.position_type
from master m
left join family f on f.source_system_code = m.source_system_code and f.id_job_family = m.id_job_family
left join fungsi g on g.source_system_code = m.source_system_code and g.id_job_function = m.id_job_function
left join {{ ref('ref_position_type_gold') }} t on t.source_system = m.source_system_code and t.kode = m.fk_position_type_id
union all
select 'UNKNOWN', 'UNKNOWN', 'Tidak diketahui', null, null, null

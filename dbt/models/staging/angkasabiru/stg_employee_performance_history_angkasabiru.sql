{#
  Mapping AB: employee_performance_history <- employee_performance.
    performance_score = konversi dari performance_rating lewat seed ref_performance_rating_angkasabiru.
  API saat ini hanya mengirim id_employee dan period_year: performance_rating belum ada, sehingga
  performance_score ikut NULL sampai rating dikirim. pct_kpi_achievement belum dikirim -> NULL.
  id_performance_history: sumber tidak menyediakan id -> kunci buatan DWH dari isi baris.
#}
select
    {{ id_employee('angkasabiru', ab('employee_performance', 'id_employee')) }} as id_employee,
    coalesce({{ ab('employee_performance', 'id_performance_history') }}, 'AB-PERF-AB-' || md5(r._row_hash)) as id_performance_history,
    {{ ke_int(ab('employee_performance', 'period_year')) }}             as period_year,
    k.performance_score                                                 as performance_score,
    {{ ab('employee_performance', 'performance_rating') }}              as performance_rating,
    {{ ke_desimal(ab('employee_performance', 'pct_kpi_achievement')) }} as pct_kpi_achievement,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_performance') }} r
left join {{ ref('ref_performance_rating_angkasabiru') }} k
       on k.source_system = 'angkasabiru'
      and lower(k.performance_rating) = lower({{ ab('employee_performance', 'performance_rating') }})

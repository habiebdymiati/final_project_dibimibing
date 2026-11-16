{#
  Mapping Angkasa Biru Retail: employee_performance_history <- performances (endpoint lama):
    id_employee <- nik;  id_performance_history <- id;  period_year <- year;
    performance_score <- performance_nilai (skala 0-5 dari API);  performance_rating <- performance_category (apa adanya).
  pct_kpi_achievement tidak punya sumber (performance_scala identik dengan performance_nilai) -> NULL.
#}
select
    {{ id_employee('angkasabiruretail', nip7(abr('performances', 'nik'))) }} as id_employee,
    {{ abr('performances', 'id') }}                   as id_performance_history,
    {{ ke_int(abr('performances', 'year')) }} as period_year,
    {{ ke_desimal(abr('performances', 'performance_nilai')) }} as performance_score,
    {{ baku('angkasabiruretail', 'performance_rating', abr('performances', 'performance_category')) }} as performance_rating,
    cast(null as numeric)                       as pct_kpi_achievement,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'performances') }} r
where {{ abr('performances', 'id') }} is not null

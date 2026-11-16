{#
  Dimensi periode penilaian talenta (katalog BRD 6.2): satu baris per semester.
  quarter = kuartal AKHIR semester (S1 -> 2, S2 -> 4), mengikuti definisi period_label BRD.
#}
select
    tahun::text || '-S' || s        as period_key,
    tahun                           as year,
    case s when 1 then 2 else 4 end as quarter,
    'Semester ' || s || ' ' || tahun as period_label
from generate_series(2020, extract(year from {{ as_of() }})::int + 1) tahun
cross join (values (1), (2)) v(s)
order by 1

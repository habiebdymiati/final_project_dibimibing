select
    d::date as date_key,
    extract(year from d)::int as year,
    extract(quarter from d)::int as quarter,
    extract(month from d)::int as month,
    (array['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'])[extract(month from d)::int] as month_name
from generate_series(date '2015-01-01', date '2035-12-31', interval '1 day') as d

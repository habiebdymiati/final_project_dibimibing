{#
  Pegawai Talent Mobility (diperbantukan antar perusahaan grup): orang yang sama — dikenali lewat
  nomor KTP (id_nik) yang identik — tercatat di dua perusahaan: non-aktif di perusahaan ASAL
  (tinggal record history, riwayat posisinya ditutup pada tanggal pindah) dan aktif di perusahaan
  TUJUAN dengan employment_type 'Talent Mobility' (kontraknya PKWTT). Grain: satu baris per orang.
  id_nik sengaja TIDAK ikut dipublikasikan ke mart.
#}
with identitas as (
    {{ dari_silver('employee_identification', 'id_employee, id_nik, dt_start_work, employment_type') }}
),
profil as (
    {{ dari_silver('employee_profile', 'id_employee, full_name, employment_status') }}
),
gabung as (
    select i.id_nik, i.kode_sumber, i.id_employee, i.dt_start_work, i.employment_type,
           p.full_name, p.employment_status
    from identitas i
    join profil p using (id_employee)
    where i.id_nik is not null
),
asal as (
    select * from gabung where employment_status <> 'aktif'
),
tujuan as (
    select * from gabung where employment_status = 'aktif' and employment_type = 'Talent Mobility'
)
select
    t.id_employee                       as id_employee,
    t.full_name                         as full_name,
    a.kode_sumber                       as company_origin_code,
    t.kode_sumber                       as company_current_code,
    a.id_employee                       as id_employee_origin,
    a.dt_start_work                     as dt_start_origin,
    t.dt_start_work                     as dt_mobility_start
from tujuan t
join asal a
  on a.id_nik = t.id_nik
 and a.kode_sumber <> t.kode_sumber

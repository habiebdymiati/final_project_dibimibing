{# Mapping ABD: employee_identification <- employee_identifications (nama kolom sama dengan target). #}
select
    {{ id_employee('abdestination', abd('employee_identifications', 'id_employee')) }} as id_employee,
    {{ abd('employee_identifications', 'id_nik') }}                       as id_nik,
    {{ hanya_angka(abd('employee_identifications', 'id_npwp')) }}         as id_npwp,
    upper({{ abd('employee_identifications', 'birth_place') }})           as birth_place,
    {{ ke_tanggal(abd('employee_identifications', 'dt_birth')) }}         as dt_birth,
    {{ ke_tanggal(abd('employee_identifications', 'dt_start_work')) }}    as dt_start_work,
    {{ ke_tanggal(abd('employee_identifications', 'dt_retirement')) }}    as dt_retirement,
    {{ ke_tanggal(abd('employee_identifications', 'dt_appointed_employee')) }} as dt_appointed_employee,
    {{ ke_tanggal(abd('employee_identifications', 'dt_grade_start')) }}   as dt_grade_start,
    {{ abd('employee_identifications', 'employment_type') }}              as employment_type,
    {{ abd('employee_identifications', 'job_class') }}                    as job_class,
    {{ abd('employee_identifications', 'gender') }}                       as gender,
    {{ ke_ponsel(abd('employee_identifications', 'mobile_phone')) }}      as mobile_phone,
    lower({{ abd('employee_identifications', 'corporate_email') }})       as corporate_email,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_identifications') }} r
where {{ abd('employee_identifications', 'id_employee') }} is not null

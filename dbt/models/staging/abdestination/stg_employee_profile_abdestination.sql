{# Mapping ABD: employee_profile <- employee_profiles (HRIS ABD memakai nama field katalog;
   nilai sudah baku). id_employee = kunci registri DWH (30 + 6 digit urut TMT); API memakai satu pengenal
   (id_employee = new_nip = old_nip). band_name: dari API bila ada, selama kosong diturunkan dari job_class
   (employee_identifications) lewat tangga band. #}
select
    {{ id_employee('abdestination', abd('employee_profiles', 'new_nip')) }} as id_employee,
    {{ abd('employee_profiles', 'old_nip') }}                  as old_nip,
    cast({{ abd('employee_profiles', 'new_nip') }} as varchar) as new_nip,
    upper({{ abd('employee_profiles', 'full_name') }})         as full_name,
    {{ abd('employee_profiles', 'academic_title') }}           as academic_title,
    lower({{ abd('employee_profiles', 'corporate_email') }})   as corporate_email,
    {{ abd('employee_profiles', 'employment_status') }}        as employment_status,
    {{ abd('employee_profiles', 'photo_blob') }}               as photo_blob,
    {{ abd('employee_profiles', 'area_name') }}                as area_name,
    {{ abd('employee_profiles', 'directorate_name') }}         as directorate_name,
    {{ abd('employee_profiles', 'org_group_name') }}           as org_group_name,
    coalesce({{ abd('employee_profiles', 'band_name') }}, b.band_name) as band_name,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_profiles') }} r
left join {{ source('raw_abd', 'employee_identifications') }} i
       on {{ abd('employee_identifications', 'id_employee', 'i') }} = {{ abd('employee_profiles', 'new_nip') }}
left join {{ ref('ref_band_abdestination') }} b
       on {{ ke_int(abd('employee_identifications', 'job_class', 'i')) }} between b.job_class_min and b.job_class_max
where {{ abd('employee_profiles', 'new_nip') }} is not null

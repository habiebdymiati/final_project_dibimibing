{# Mapping ABD: employee_family_member <- employee_family_members (nilai gender/relasi sudah baku). #}
select
    {{ id_employee('abdestination', abd('employee_family_members', 'id_employee')) }} as id_employee,
    {{ abd('employee_family_members', 'id_family_member') }}  as id_family_member,
    upper({{ abd('employee_family_members', 'full_name') }})  as full_name,
    {{ abd('employee_family_members', 'relationship_type') }} as relationship_type,
    {{ abd('employee_family_members', 'gender') }}            as gender,
    upper({{ abd('employee_family_members', 'birth_place') }}) as birth_place,
    {{ ke_tanggal(abd('employee_family_members', 'dt_birth')) }} as dt_birth,
    {{ abd('employee_family_members', 'id_type') }}           as id_type,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_family_members') }} r
where {{ abd('employee_family_members', 'id_family_member') }} is not null

{# Mapping AB: employee_family_member <- employee_family_member. id_type belum dikirim API -> NULL. #}
select
    {{ id_employee('angkasabiru', ab('employee_family_member', 'id_employee')) }} as id_employee,
    {{ ab('employee_family_member', 'id_family_member') }}    as id_family_member,
    upper({{ ab('employee_family_member', 'full_name') }}) as full_name,
    {{ baku('angkasabiru', 'relationship_type', ab('employee_family_member', 'relationship_type')) }} as relationship_type,
    {{ baku('angkasabiru', 'gender', ab('employee_family_member', 'gender')) }} as gender,
    upper({{ ab('employee_family_member', 'birth_place') }}) as birth_place,
    {{ ke_tanggal(ab('employee_family_member', 'dt_birth')) }} as dt_birth,
    {{ ab('employee_family_member', 'id_type') }}             as id_type,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_family_member') }} r
where {{ ab('employee_family_member', 'id_family_member') }} is not null

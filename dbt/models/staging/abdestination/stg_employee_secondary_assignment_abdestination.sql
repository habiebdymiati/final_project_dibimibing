{# Mapping ABD (katalog BRD 2.10): employee_secondary_assignment <- employee_secondary_assignments. #}
select
    {{ abd('employee_secondary_assignments', 'id_secondary_assignment') }} as id_secondary_assignment,
    {{ id_employee('abdestination', abd('employee_secondary_assignments', 'new_nip')) }} as id_employee,
    {{ abd('employee_secondary_assignments', 'fk_position_variant_id') }}  as fk_position_variant_id,
    {{ abd('employee_secondary_assignments', 'position_name') }}           as position_name,
    {{ abd('employee_secondary_assignments', 'job_class') }}               as job_class,
    {{ abd('employee_secondary_assignments', 'org_unit_name') }}           as org_unit_name,
    {{ abd('employee_secondary_assignments', 'company_name') }}            as company_name,
    {{ abd('employee_secondary_assignments', 'secondary_assignment_type') }} as secondary_assignment_type,
    {{ abd('employee_secondary_assignments', 'assignment_letter_number') }} as assignment_letter_number,
    {{ ke_tanggal(abd('employee_secondary_assignments', 'dt_assignment_letter')) }} as dt_assignment_letter,
    {{ ke_tanggal(abd('employee_secondary_assignments', 'dt_assignment_start')) }}  as dt_assignment_start,
    {{ ke_tanggal(abd('employee_secondary_assignments', 'dt_assignment_end')) }}    as dt_assignment_end,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'employee_secondary_assignments') }} r
where {{ abd('employee_secondary_assignments', 'id_secondary_assignment') }} is not null

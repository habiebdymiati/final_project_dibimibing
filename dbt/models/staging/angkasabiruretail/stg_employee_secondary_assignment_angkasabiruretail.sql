{#
  Mapping Angkasa Biru Retail (katalog BRD 2.10): employee_secondary_assignment <- employee-assignment-histories (turunan).
    fk_position_variant_id <- code_positions;  position_name <- assignment_position;
    secondary_assignment_type <- assignment_name (turunan).
  id_employee endpoint ini berisi NIP LAMA -> dipetakan ke kunci pegawai DWH.
#}
select
    'AB-ASG-ABR-' || {{ abr('employee__assignment__histories', 'id_assignment_history') }} as id_secondary_assignment,
    {{ id_employee('angkasabiruretail', nip7(abr('employee__assignment__histories', 'id_employee'))) }} as id_employee,
    {{ abr('employee__assignment__histories', 'code_positions') }}        as fk_position_variant_id,
    {{ abr('employee__assignment__histories', 'assignment_position') }}   as position_name,
    cast(null as text)                                                    as job_class,
    cast(null as text)                                                    as org_unit_name,
    cast(null as text)                                                    as company_name,
    {{ abr('employee__assignment__histories', 'assignment_name') }}       as secondary_assignment_type,
    {{ abr('employee__assignment__histories', 'assignment_letter_number') }} as assignment_letter_number,
    cast(null as date)                                                    as dt_assignment_letter,
    {{ ke_tanggal(abr('employee__assignment__histories', 'dt_assignment_start')) }} as dt_assignment_start,
    {{ ke_tanggal(abr('employee__assignment__histories', 'dt_assignment_end')) }}   as dt_assignment_end,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'employee__assignment__histories') }} r
where {{ abr('employee__assignment__histories', 'id_assignment_history') }} is not null

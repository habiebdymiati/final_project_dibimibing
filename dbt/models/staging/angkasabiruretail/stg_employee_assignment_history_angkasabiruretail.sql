{#
  Mapping Angkasa Biru Retail: employee_assignment_history <- employee-assignment-histories (nama kolom sama dengan target).
  id_employee: kolom id_employee endpoint ini berisi NIP LAMA (bukan ID sistem baru) -> dipetakan ke kunci pegawai DWH.
  assignment_letter_blob <- assignment_letter_filename (API mengirim nama berkas surat, bukan isinya).
#}
select
    {{ id_employee('angkasabiruretail', nip7(abr('employee__assignment__histories', 'id_employee'))) }} as id_employee,
    {{ abr('employee__assignment__histories', 'id_assignment_history') }}      as id_assignment_history,
    {{ abr('employee__assignment__histories', 'assignment_name') }}            as assignment_name,
    {{ abr('employee__assignment__histories', 'assignment_position') }}        as assignment_position,
    {{ abr('employee__assignment__histories', 'assignment_letter_number') }}   as assignment_letter_number,
    {{ abr('employee__assignment__histories', 'assignment_letter_filename') }} as assignment_letter_blob,
    {{ ke_tanggal(abr('employee__assignment__histories', 'dt_assignment_start')) }} as dt_assignment_start,
    {{ ke_tanggal(abr('employee__assignment__histories', 'dt_assignment_end')) }}   as dt_assignment_end,
    {{ ke_int(abr('employee__assignment__histories', 'assignment_duration_months')) }} as assignment_duration_months,
    {{ abr('employee__assignment__histories', 'description') }}                as description,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'employee__assignment__histories') }} r
where {{ abr('employee__assignment__histories', 'id_assignment_history') }} is not null

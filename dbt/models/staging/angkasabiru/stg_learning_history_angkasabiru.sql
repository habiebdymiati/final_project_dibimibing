{#
  Mapping AP (katalog BRD 4.3): learning_history <- employee_learning.
  id_learning, is_mandatory, score, dt_expiry tidak ada di API asli -> dilengkapi instance tiruan (mock);
  bila kosong, id_learning dibuat dari isi baris.
#}
select distinct
    {{ id_employee('angkasabiru', ab('employee_learning', 'id_employee')) }} as id_employee,
    coalesce({{ ab('employee_learning', 'id_learning') }}, 'AB-LRN-AB-' || md5(r._row_hash)) as id_learning,
    {{ ab('employee_learning', 'learning_name') }}                    as learning_name,
    {{ baku('angkasabiru', 'learning_type', ab('employee_learning', 'learning_type')) }} as learning_type,
    coalesce({{ ke_boolean(ab('employee_learning', 'is_mandatory')) }}, false) as is_mandatory,
    {{ ke_tanggal(ab('employee_learning', 'dt_completion')) }}        as dt_completion,
    {{ ke_tanggal(ab('employee_learning', 'dt_expiry')) }}            as dt_expiry,
    {{ ke_desimal(ab('employee_learning', 'score')) }}                as score,
    {{ ke_int(ab('employee_learning', 'learning_hours')) }}           as learning_hours,
    {{ ab('employee_learning', 'provider') }}                         as provider,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'employee_learning') }} r
where {{ ab('employee_learning', 'learning_name') }} is not null

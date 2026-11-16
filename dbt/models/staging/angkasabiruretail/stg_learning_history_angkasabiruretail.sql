{#
  Mapping Angkasa Biru Retail (katalog BRD 4.3): learning_history <- gabungan trainings + learnings.
    trainings : endpoint lama; tidak punya is_mandatory/score/learning_hours/dt_expiry.
    learnings : endpoint baru; field lengkap. API asli hanya mengirim 1 baris -> dilengkapi mock.
  id_employee kedua endpoint berisi NIP LAMA -> dipetakan ke kunci pegawai DWH.
#}
select
    {{ id_employee('angkasabiruretail', nip7(abr('trainings', 'nik'))) }} as id_employee,
    'TRN-' || {{ abr('trainings', 'id') }}                as id_learning,
    {{ abr('trainings', 'training_name') }}               as learning_name,
    {{ baku('angkasabiruretail', 'learning_type', abr('trainings', 'training_type')) }} as learning_type,
    cast(null as boolean)                                 as is_mandatory,
    {{ ke_tanggal(abr('trainings', 'end_date')) }}        as dt_completion,
    cast(null as date)                                    as dt_expiry,
    cast(null as numeric)                                 as score,
    cast(null as integer)                                 as learning_hours,
    {{ abr('trainings', 'training_org') }}                as provider,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'trainings') }} r
where {{ abr('trainings', 'id') }} is not null
union all
select
    {{ id_employee('angkasabiruretail', nip7(abr('learnings', 'id_employee'))) }} as id_employee,
    {{ abr('learnings', 'id_learning') }}                 as id_learning,
    {{ abr('learnings', 'learning_name') }}               as learning_name,
    {{ baku('angkasabiruretail', 'learning_type', abr('learnings', 'learning_type')) }} as learning_type,
    {{ ke_boolean(abr('learnings', 'is_mandatory')) }}    as is_mandatory,
    {{ ke_tanggal(abr('learnings', 'dt_completion')) }}   as dt_completion,
    {{ ke_tanggal(abr('learnings', 'dt_expiry')) }}       as dt_expiry,
    {{ ke_desimal(abr('learnings', 'score')) }}           as score,
    {{ ke_int(abr('learnings', 'learning_hours')) }}      as learning_hours,
    {{ abr('learnings', 'provider') }}                    as provider,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'learnings') }} r
where {{ abr('learnings', 'id_learning') }} is not null

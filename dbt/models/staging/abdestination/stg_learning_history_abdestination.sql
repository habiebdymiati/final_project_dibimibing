{# Mapping ABD (katalog BRD 4.3): learning_history <- learning_histories (transaction/learning-histories). #}
select
    {{ id_employee('abdestination', abd('learning_histories', 'id_employee')) }} as id_employee,
    {{ abd('learning_histories', 'id_learning') }}            as id_learning,
    {{ abd('learning_histories', 'learning_name') }}          as learning_name,
    {{ abd('learning_histories', 'learning_type') }}          as learning_type,
    coalesce({{ ke_boolean(abd('learning_histories', 'is_mandatory')) }}, false) as is_mandatory,
    {{ ke_tanggal(abd('learning_histories', 'dt_completion')) }} as dt_completion,
    {{ ke_tanggal(abd('learning_histories', 'dt_expiry')) }}  as dt_expiry,
    {{ ke_desimal(abd('learning_histories', 'score')) }}      as score,
    {{ ke_int(abd('learning_histories', 'learning_hours')) }} as learning_hours,
    {{ abd('learning_histories', 'provider') }}               as provider,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'learning_histories') }} r
where {{ abd('learning_histories', 'id_learning') }} is not null

{# Mapping ABD: position_competency_requirement <- position_competency_requirements (nama kolom sama). #}
select
    {{ abd('position_competency_requirements', 'id_position_master') }}  as id_position_master,
    {{ abd('position_competency_requirements', 'id_competency') }}       as id_competency,
    {{ abd('position_competency_requirements', 'competency_name') }}     as competency_name,
    {{ abd('position_competency_requirements', 'competency_category') }} as competency_category,
    {{ abd('position_competency_requirements', 'required_level') }}      as required_level,
    {{ kolom_teknis('abdestination') }}
from {{ source('raw_abd', 'position_competency_requirements') }} r
where {{ abd('position_competency_requirements', 'id_competency') }} is not null

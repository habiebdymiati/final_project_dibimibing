{#
  Mapping Angkasa Biru Retail: position_competency_requirement <- competences (id_competency <- code, competency_name <- competency,
  competency_category <- type).
  PERHATIAN: Angkasa Biru Retail hanya punya MASTER kompetensi. API tidak mengirim kompetensi mana dibutuhkan posisi mana dan pada
  level berapa, jadi id_position_master dan required_level NULL. Tabel ini memuat daftar kompetensi, belum kebutuhan per posisi.
#}
select
    cast(null as text)                 as id_position_master,
    {{ abr('competences', 'code') }}         as id_competency,
    {{ baku('angkasabiruretail', 'competency_name', abr('competences', 'competency')) }} as competency_name,
    {{ abr('competences', 'type') }}         as competency_category,
    cast(null as text)                 as required_level,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'competences') }} r
where {{ abr('competences', 'code') }} is not null

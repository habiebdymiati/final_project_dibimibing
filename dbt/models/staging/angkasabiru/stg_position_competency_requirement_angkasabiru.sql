{#
  Mapping AB: position_competency_requirement <- position_competency_requirements
  (id_competency, competency_name, competency_category, required_level).
  competency_name: kolom di raw bernama "competetency_name" (salah ketik di API).
  id_position_master (keputusan 06 Nov 2026, menggantikan nama fk_position_id): posisi pemilik kebutuhan kompetensi,
  merujuk position_master.id_position_master. Diambil dari kolom raw fk_position_id; di master Angkasa Biru kode
  posisi, master posisi, dan varian posisi sama persis, jadi nilainya langsung berupa id_position_master.
  Baris kembar identik disatukan.
#}
select distinct
    {{ ab('position_competency_requirements', 'fk_position_id') }}      as id_position_master,
    {{ ab('position_competency_requirements', 'id_competency') }}       as id_competency,
    {{ ab('position_competency_requirements', ['competency_name', 'competetency_name']) }} as competency_name,
    {{ baku('angkasabiru', 'competency_category', ab('position_competency_requirements', 'competency_category')) }} as competency_category,
    {{ ab('position_competency_requirements', 'required_level') }}      as required_level,
    {{ kolom_teknis('angkasabiru') }}
from {{ source('raw_ab', 'position_competency_requirements') }} r

{#
  Mapping Angkasa Biru Retail (katalog BRD 4.5): competency_assessment <- assessment_results (+ assessment_result_by_competences).
    job_fit_score     <- hasil_ases (turunan): nilai angka dipakai langsung; hasil kategorikal dipetakan ke
                         skor 0-100 (Disarankan 90, Memenuhi Persyaratan 85, Disarankan dengan Pengembangan 75,
                         Memenuhi Persyaratan dengan Catatan 70, Dipertimbangkan 60, Belum Memenuhi Persyaratan 45,
                         Belum Sesuai dengan Kriteria Jabatan Saat Ini 40); kategori aslinya dibawa di assessment_result
    competency_gap    <- rata-rata result anak per asesmen (turunan assessment_result_by_competences)
    assessment_period <- tahun berlaku_dari (turunan);  dt_assessment <- berlaku_dari
    assessment_method : tidak ada di API asli -> dilengkapi instance tiruan (mock)
  id_employee: nik endpoint ini berisi NIP LAMA -> dipetakan ke kunci pegawai DWH.
#}
with gap as (
    select {{ abr('assessment_result_by_competences', 'id_parent') }} as id_parent,
           avg({{ ke_desimal(abr('assessment_result_by_competences', 'result')) }}) as competency_gap
    from {{ source('raw_abr', 'assessment_result_by_competences') }} r
    group by 1
)
select
    {{ id_employee('angkasabiruretail', nip7(abr('assessment_results', 'nik'))) }} as id_employee,
    to_char({{ ke_tanggal(abr('assessment_results', 'berlaku_dari')) }}, 'YYYY') as assessment_period,
    coalesce({{ ke_desimal(abr('assessment_results', 'hasil_ases')) }},
             case lower({{ abr('assessment_results', 'hasil_ases') }})
                  when 'disarankan'                                    then 90
                  when 'memenuhi persyaratan'                          then 85
                  when 'disarankan dengan pengembangan'                then 75
                  when 'memenuhi persyaratan dengan catatan'           then 70
                  when 'dipertimbangkan'                               then 60
                  when 'belum memenuhi persyaratan'                    then 45
                  when 'belum sesuai dengan kriteria jabatan saat ini' then 40
                  when 'sudah sesuai dengan kriteria jabatan saat ini' then 85
                  when 'sesuai dengan kriteria jabatan saat ini'       then 85
                  when 'kurang disarankan'                             then 50
                  when 'tidak disarankan'                              then 35
             end)                                                    as job_fit_score,
    {{ abr('assessment_results', 'hasil_ases') }}                    as assessment_result,
    g.competency_gap,
    {{ abr('assessment_results', 'assessment_method') }}             as assessment_method,
    {{ ke_tanggal(abr('assessment_results', 'berlaku_dari')) }}      as dt_assessment,
    {{ kolom_teknis('angkasabiruretail') }}
from {{ source('raw_abr', 'assessment_results') }} r
left join gap g on g.id_parent = {{ abr('assessment_results', 'id') }}
where {{ abr('assessment_results', 'id') }} is not null

{#
  Analitik talenta per pegawai AKTIF per periode (semester), sesuai katalog BRD 6.2 dan lampiran 7.1-7.2.

  Komponen EQS (skala 0-100) dan bobotnya (lampiran 7.1):
    kinerja    25%  rata-rata skor kinerja 3 tahun, dinormalkan per sumber (AP skala 0-120, Angkasa Biru Retail 0-5)
    kompetensi 20%  job_fit_score periode terbaru (competency_assessment)
    pengalaman 15%  masa kerja pada job family yang sama; 120 bulan (10 tahun) dihitung 100
    aspirasi   30%  career_aspiration milik Rinjani (inbound) -> BELUM ADA sumbernya, NULL
    pelatihan  10%  completion rate pelatihan wajib/penjenjangan (learning_history.is_mandatory)
    rekam_jejak 5%  100 tanpa catatan disiplin aktif, 0 bila ada
  eqs_score = rata-rata tertimbang komponen yang TERSEDIA (bobot dinormalkan ulang; aspirasi menunggu Rinjani).

  Sumbu 9-Box (lampiran 7.2): performance = 95% kinerja + 5% rekam jejak; capacity = 80% kompetensi + 20% learning
  agility (bobot dinormalkan ulang bila salah satu kosong). Tingkat: < 60 Low, 60-79 Medium, >= 80 High;
  tanpa data sama sekali masuk nine_box_key 0 (Unclassified).
  Penomoran sel mengikuti kisi acuan Rinjani (lihat dim_nine_box): per kolom performance dari kiri-bawah,
  1 Unfit ... 9 High Potential.

  Grain: satu baris per pegawai per period_key; run pada periode yang sama menimpa baris periode itu saja.
#}
{{ config(
    materialized='incremental',
    incremental_strategy='append',
    full_refresh=false,
    pre_hook="{% if is_incremental() %}delete from {{ this }} where period_key = " ~ periode_kini() ~ "{% else %}select 1{% endif %}"
) }}

with metrik as (
    select *,
           case source_system_code
                when 'angkasabiru'       then least(100, performance_score_avg_3y / 1.2)
                when 'angkasabiruretail' then least(100, performance_score_avg_3y * 20)
                when 'abdestination'       then least(100, performance_score_avg_3y)
           end as kinerja,
           least(100, job_fit_score)                                        as kompetensi,
           least(100, tenure_in_job_family_months / 120.0 * 100)            as pengalaman,
           cast(null as numeric)                                            as aspirasi,
           pct_mandatory_training                                           as pelatihan,
           case when has_active_disciplinary then 0 else 100 end::numeric   as rekam_jejak
    from {{ ref('int_employee_metrics') }}
    where employment_status = 'aktif'
),
komponen as (
    select *,
           (coalesce(kinerja, 0)    * 0.25 + coalesce(kompetensi, 0) * 0.20 + coalesce(pengalaman, 0) * 0.15 +
            coalesce(aspirasi, 0)   * 0.30 + coalesce(pelatihan, 0)  * 0.10 + coalesce(rekam_jejak, 0) * 0.05)
           / nullif((case when kinerja     is not null then 0.25 else 0 end +
                     case when kompetensi  is not null then 0.20 else 0 end +
                     case when pengalaman  is not null then 0.15 else 0 end +
                     case when aspirasi    is not null then 0.30 else 0 end +
                     case when pelatihan   is not null then 0.10 else 0 end +
                     case when rekam_jejak is not null then 0.05 else 0 end), 0) as eqs,
           (coalesce(kinerja, 0) * 0.95 + coalesce(rekam_jejak, 0) * 0.05)
           / nullif((case when kinerja     is not null then 0.95 else 0 end +
                     case when rekam_jejak is not null then 0.05 else 0 end), 0) as sumbu_performance,
           (coalesce(kompetensi, 0) * 0.80 + coalesce(learning_agility_score, 0) * 0.20)
           / nullif((case when kompetensi             is not null then 0.80 else 0 end +
                     case when learning_agility_score is not null then 0.20 else 0 end), 0) as sumbu_capacity
    from metrik
),
tingkat as (
    select *,
           case when sumbu_performance is null then null
                when sumbu_performance >= 80 then 3 when sumbu_performance >= 60 then 2 else 1 end as tk_performance,
           case when sumbu_capacity is null then null
                when sumbu_capacity >= 80 then 3 when sumbu_capacity >= 60 then 2 else 1 end as tk_capacity
    from komponen
)
select
    id_employee || '|' || {{ periode_kini() }} as talent_key,
    id_employee                                as employee_key,
    {{ periode_kini() }}                       as period_key,
    coalesce(case                                           -- penomoran sel kisi acuan (dim_nine_box)
                  when tk_performance = 1 and tk_capacity = 1 then 1
                  when tk_performance = 1 and tk_capacity = 2 then 2
                  when tk_performance = 1 and tk_capacity = 3 then 4
                  when tk_performance = 2 and tk_capacity = 1 then 3
                  when tk_performance = 2 and tk_capacity = 2 then 5
                  when tk_performance = 2 and tk_capacity = 3 then 7
                  when tk_performance = 3 and tk_capacity = 1 then 6
                  when tk_performance = 3 and tk_capacity = 2 then 8
                  when tk_performance = 3 and tk_capacity = 3 then 9
             end, 0)                                    as nine_box_key,
    round(sumbu_performance, 1)                as performance_axis_score,
    round(sumbu_capacity, 1)                   as capacity_axis_score,
    round(eqs, 1)                              as eqs_score,
    round(kinerja, 1)                          as kinerja_component,
    round(kompetensi, 1)                       as kompetensi_component,
    round(pengalaman, 1)                       as pengalaman_component,
    round(aspirasi, 1)                         as aspirasi_component,
    round(pelatihan, 1)                        as pelatihan_component,
    round(rekam_jejak, 1)                      as rekam_jejak_component,
    is_top_talent                              as is_in_talent_pool,
    cast(null as integer)                      as talent_pool_ranking,
    is_top_talent
from tingkat

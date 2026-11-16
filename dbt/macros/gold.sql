{# Tanggal acuan snapshot: var as_of_date, bila kosong tanggal hari ini. #}
{% macro as_of() -%}
    {%- if var('as_of_date') -%}date '{{ var("as_of_date") }}'{%- else -%}current_date{%- endif -%}
{%- endmacro %}

{# Kunci periode (semester) dari tanggal acuan: '2026-S1' untuk Januari-Juni, '2026-S2' untuk Juli-Desember. #}
{% macro periode_kini() -%}
    (to_char({{ as_of() }}, 'YYYY') || '-S' || case when extract(month from {{ as_of() }}) <= 6 then 1 else 2 end)
{%- endmacro %}

{# Selisih bulan penuh antara dua tanggal; NULL bila salah satunya NULL atau urutan terbalik. #}
{% macro months_between(from_date, to_date) -%}
    (case when ({{ from_date }}) is null or ({{ to_date }}) is null or ({{ from_date }}) > ({{ to_date }}) then null
          else (extract(year from age(({{ to_date }})::date, ({{ from_date }})::date)) * 12
                + extract(month from age(({{ to_date }})::date, ({{ from_date }})::date)))::int end)
{%- endmacro %}

{#
  Gabungkan satu entitas silver dari semua sumber pada var gold_sources.
  Tiap baris membawa source_system_code (angkasabiru, angkasabiruretail) dan kode_sumber (API, SNH) untuk membentuk kunci gold:
  id milik sumber (unit, posisi) bisa saja sama antar perusahaan, jadi kuncinya selalu diawali kode sumber.
#}
{% macro dari_silver(entitas, kolom) %}
{% for s, kode in var('gold_sources').items() %}
    select cast('{{ s }}' as text) as source_system_code, cast('{{ kode }}' as text) as kode_sumber, {{ kolom }}
    from {{ source('fdw_' ~ s, entitas ~ '_' ~ s) }}
    {% if not loop.last %}union all{% endif %}
{% endfor %}
{% endmacro %}

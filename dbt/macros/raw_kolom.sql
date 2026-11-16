{#
  Ambil satu kolom dari raw_table_<sumber>.<tabel> SESUAI BERKAS MAPPING.

  kolom : nama kolom pada berkas mapping, atau daftar kandidat [nama_di_mapping, nama_asli_di_raw, ...].
          Dipakai kandidat pertama yang BENAR-BENAR ADA di tabel raw.
  Bila tidak satu pun ada (API belum mengirim field itu) hasilnya NULL, bukan error dan bukan tebakan.
  Begitu API mulai mengirim kolomnya, flatten menambah kolom di raw_table_ dan model ini otomatis mengisinya.

  Nilai dirapikan seragam untuk semua sumber lewat public.bersih_teks: spasi berlebih dan ganti baris dibuang, teks kosong dan
  penanda kosong ('-', 'null', 'n/a', 'none', 'tidak ada') menjadi NULL.
#}
{% macro raw_kolom(sumber, tabel, kolom, alias='r') -%}
    {%- set kandidat = [kolom] if kolom is string else kolom -%}
    {%- set ns = namespace(hasil=none) -%}
    {%- if execute -%}
        {%- set rel = adapter.get_relation(database=target.database, schema='raw_table_' ~ sumber, identifier=tabel) -%}
        {%- if rel -%}
            {%- set ada = adapter.get_columns_in_relation(rel) | map(attribute='name') | list -%}
            {%- for k in kandidat -%}
                {%- if ns.hasil is none and k in ada -%}{%- set ns.hasil = k -%}{%- endif -%}
            {%- endfor -%}
        {%- endif -%}
    {%- endif -%}
    {%- if ns.hasil is none -%}
        cast(null as text)
    {%- else -%}
        public.bersih_teks({{ alias }}.{{ adapter.quote(ns.hasil) }})
    {%- endif -%}
{%- endmacro %}

{# Singkatan untuk sumber Angkasa Biru. #}
{% macro ab(tabel, kolom, alias='r') -%}
    {{ raw_kolom('angkasabiru', tabel, kolom, alias) }}
{%- endmacro %}

{# Singkatan untuk sumber Angkasa Biru Retail. Nama tabel raw memakai garis bawah ganda untuk tanda hubung endpoint (employee-profile -> employee__profile). #}
{% macro abr(tabel, kolom, alias='r') -%}
    {{ raw_kolom('angkasabiruretail', tabel, kolom, alias) }}
{%- endmacro %}

{# Singkatan untuk sumber Angkasa Biru LMS (sistem grup lintas perusahaan). #}
{% macro lms(tabel, kolom, alias='r') -%}
    {{ raw_kolom('lms', tabel, kolom, alias) }}
{%- endmacro %}

{# Singkatan untuk sumber Angkasa Biru Destinasi. #}
{% macro abd(tabel, kolom, alias='r') -%}
    {{ raw_kolom('abdestination', tabel, kolom, alias) }}
{%- endmacro %}

{# NIP lama Angkasa Biru Retail selalu 7 digit; beberapa baris sumber kehilangan nol di depan -> dikembalikan. #}
{% macro nip7(e) -%}
    case when ({{ e }}) ~ '^[0-9]{1,6}$' then lpad(({{ e }}), 7, '0') else ({{ e }}) end
{%- endmacro %}

{# Kolom teknis DWH yang dibawa setiap model staging. #}
{% macro kolom_teknis(sumber, alias='r') -%}
    cast('{{ sumber }}' as text) as dwh_source_system,
    {{ alias }}._batch_id         as dwh_batch_id,
    {{ alias }}._extracted_at     as dwh_extracted_at
{%- endmacro %}

{#
  Kunci pegawai buatan DWH (VARCHAR berisi 8 digit, lihat models/registry/registry_id_employee_angkasabiru.sql).
  Dicari di registri berdasarkan NIP, jadi nilainya sama di semua tabel dan relasinya utuh.
#}
{% macro id_employee(sumber, nip) -%}
    (select g.id_employee from {{ ref('registry_id_employee_' ~ sumber) }} g
      where g.source_system = '{{ sumber }}' and g.nip = {{ nip }})
{%- endmacro %}

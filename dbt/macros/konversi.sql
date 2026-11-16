{# Konversi tipe yang AMAN: nilai yang tidak bisa dikonversi menjadi NULL, tidak menggagalkan run. #}

{% macro ke_int(e) -%}
    case when ({{ e }}) ~ '^-?[0-9]{1,9}$' then ({{ e }})::integer end
{%- endmacro %}

{# desimal: koma desimal ("3,5") diterima; teks seperti "A" atau "-" menjadi NULL #}
{% macro ke_desimal(e) -%}
    case when replace(replace(({{ e }}), ' ', ''), ',', '.') ~ '^-?[0-9]+(\.[0-9]+)?$'
         then replace(replace(({{ e }}), ' ', ''), ',', '.')::numeric end
{%- endmacro %}

{% macro ke_tanggal(e) -%}
    public.try_date({{ e }})
{%- endmacro %}

{% macro ke_boolean(e) -%}
    case lower({{ e }}) when 'true' then true when '1' then true when 'y' then true when 'ya' then true
                        when 'false' then false when '0' then false when 'n' then false when 'tidak' then false end
{%- endmacro %}

{#
  Standarisasi nomor ponsel (mapping: "semua diawali 08 dilanjutkan nomor telepon").
    - bila ada beberapa nomor dipisah "/", dipakai yang pertama;
    - semua karakter selain angka dibuang (spasi, +, -, titik, tanda petik);
    - awalan 62 / 8 diubah menjadi 08; yang sudah 08 dibiarkan;
    - hasil yang bukan nomor ponsel (tidak berawalan 08, atau panjangnya di luar 10-14 digit) menjadi NULL.
#}
{% macro ke_ponsel(e) -%}
    (select case when n ~ '^08[0-9]{8,12}$' then n end
     from (select case when d ~ '^62' then '0' || substr(d, 3)
                       when d ~ '^8'  then '0' || d
                       else d end as n
           from (select regexp_replace(split_part({{ e }}, '/', 1), '[^0-9]', '', 'g') as d) a) b)
{%- endmacro %}

{#
  HARMONISASI: ubah nilai sumber menjadi nilai baku lintas perusahaan lewat seed map_nilai_<sumber>.
  Pencocokan tanpa membedakan huruf besar/kecil. Nilai yang belum terdaftar diteruskan apa adanya, tidak dihapus,
  dan tertangkap uji accepted_values sebagai peringatan supaya aturannya bisa ditambah.
#}
{% macro baku(sumber, kolom, e) -%}
    coalesce((select m.nilai_baku from {{ ref('map_nilai_' ~ sumber) }} m
               where m.kolom = '{{ kolom }}' and m.nilai_sumber = lower({{ e }})), {{ e }})
{%- endmacro %}

{# Hanya digit (NPWP): tanda baca dibuang supaya format semua sumber sama. #}
{% macro hanya_angka(e) -%}
    nullif(regexp_replace({{ e }}, '[^0-9]', '', 'g'), '')
{%- endmacro %}

{# Fungsi bantu di database (schema public, dipakai semua sumber; dibuat sekali tiap run, sebelum model). #}
{% macro buat_fungsi_bantu() %}
    {% if target.name != 'dwh' %}select 1{% else %}
    create or replace function public.bersih_teks(v text) returns text language sql immutable as $$
        select case when lower(t) in ('', '-', '--', 'null', 'n/a', 'none', 'tidak ada') then null else t end
        from (select btrim(regexp_replace(v, '\s+', ' ', 'g')) as t) x
    $$;
    create or replace function public.try_date(v text) returns date language plpgsql stable as $$
    declare d date;
    begin
        v := nullif(btrim(v), '');
        if v is null then return null; end if;
        -- stempel waktu ISO berzona UTC (mis. 2020-01-31T17:00:00.000Z = 1 Feb 2020 WIB) -> tanggal WIB
        if v ~ '^\d{4}-\d{2}-\d{2}T' then d := (v::timestamptz at time zone 'Asia/Jakarta')::date;
        elsif v ~ '^\d{4}-\d{2}-\d{2}$' then d := v::date;
        elsif v ~ '^\d{2}/\d{2}/\d{4}$' then d := to_date(v, 'DD/MM/YYYY');
        end if;
        -- tanggal placeholder (1900 ke bawah) bukan tanggal sebenarnya
        if d <= date '1900-01-01' then return null; end if;
        return d;
    exception when others then
        return null;
    end $$;
    {% endif %}
{% endmacro %}

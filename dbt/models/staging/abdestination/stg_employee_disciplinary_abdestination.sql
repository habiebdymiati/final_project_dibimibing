{# Mapping ABD: employee_disciplinary TIDAK punya sumber pada API HRIS ABD -> tabel terbentuk tanpa baris. #}
select
    cast(null as varchar) as id_employee,
    cast(null as text)    as disciplinary_type,
    cast(null as date)    as dt_disciplinary,
    cast(null as date)    as dt_disciplinary_end,
    cast(null as boolean) as is_aktif,
    cast('abdestination' as text) as dwh_source_system,
    cast(null as text)          as dwh_batch_id,
    cast(null as timestamptz)   as dwh_extracted_at
where false

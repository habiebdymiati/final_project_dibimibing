{# Mapping AB: employee_contract TIDAK punya sumber (kolom Source kosong) -> tabel terbentuk tanpa baris. #}
select
    cast(null as text) as id_contract,
    cast(null as varchar) as id_employee,
    cast(null as text) as contract_number,
    cast(null as text) as contract_type,
    cast(null as date) as dt_contract_start,
    cast(null as date) as dt_contract_end,
    cast(null as text) as contract_status,
    cast('angkasabiru' as text) as dwh_source_system,
    cast(null as text)          as dwh_batch_id,
    cast(null as timestamptz)   as dwh_extracted_at
where false

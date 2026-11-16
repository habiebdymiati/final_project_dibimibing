{#
  Grain: satu baris per pegawai aktif per tanggal snapshot. Riwayat snapshot dipertahankan: run pada tanggal yang sama
  menimpa baris tanggal itu, tanggal lain tidak disentuh. full_refresh=false mencegah riwayat terhapus tanpa sengaja.
#}
{{ config(
    materialized='incremental',
    incremental_strategy='append',
    full_refresh=false,
    on_schema_change='append_new_columns',
    pre_hook="{% if is_incremental() %}delete from {{ this }} where date_key = " ~ as_of() ~ "{% else %}select 1{% endif %}"
) }}

select
    id_employee || '|' || to_char({{ as_of() }}, 'YYYYMMDD') as snapshot_key,
    id_employee as employee_key,
    position_variant_key,
    org_unit_key,
    company_key,
    {{ as_of() }} as date_key,
    contract_type_key,
    tenure_in_position_months,
    tenure_in_grade_months,
    tenure_in_company_months,
    performance_score_avg_3y,
    job_fit_score,
    learning_agility_score,
    is_mandatory_training_complete,
    is_top_talent,
    has_active_disciplinary,
    contract_expiry_date
from {{ ref('int_employee_metrics') }}
where employment_status = 'aktif'

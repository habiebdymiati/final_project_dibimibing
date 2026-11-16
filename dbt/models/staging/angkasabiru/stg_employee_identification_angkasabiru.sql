{#
  Mapping AB: employee_identification <- employee_identification, kecuali:
    job_class    <- position_variants.job_class dari varian posisi TERAKHIR yang dimiliki pegawai (per new_nip);
                    pegawai tanpa varian posisi memakai job_class baris riwayat posisi terakhirnya (keputusan 06 Nov 2026)
    dt_grade_start : nilai API; bila API kosong -> tanggal mulai posisi terakhir pada riwayat posisi (keputusan 06 Nov 2026).
                    Pada pegawai yang nilai API-nya ada, keduanya selalu sama.
    dt_birth              <- reference_angkasabiru.tmt_karyawan_angkasabiru.tanggal_lahir  (keputusan 06 Nov 2026)
    dt_appointed_employee <- reference_angkasabiru.tmt_karyawan_angkasabiru.tmt_karyawan   (keputusan 06 Nov 2026)
                  API tidak mengirim tanggal lahir dan mengirim dt_appointed_employee kosong; berkas referensi menjadi
                  sumbernya. Nilai API hanya dipakai bila pegawai tidak ada di berkas referensi.
    mobile_phone : distandarkan (awalan 08); kolom di raw bernama "home_phone"
  id_employee  : kunci pegawai DWH dari registri (sama dengan employee_profile) agar relasinya utuh.
  Stempel waktu ISO (..T17:00:00.000Z) dikonversi ke tanggal WIB. id_employee kembar disatukan.
#}
select distinct on (id_employee)
    id_employee, id_nik, id_npwp, birth_place, dt_birth, dt_start_work, dt_retirement, dt_appointed_employee,
    dt_grade_start, employment_type, job_class, gender, mobile_phone, corporate_email,
    dwh_source_system, dwh_batch_id, dwh_extracted_at
from (
    select
        {{ id_employee('angkasabiru', ab('employee_identification', 'id_employee')) }} as id_employee,
        {{ ab('employee_identification', 'id_nik') }}                            as id_nik,
        {{ hanya_angka(ab('employee_identification', 'id_npwp')) }} as id_npwp,
        upper({{ ab('employee_identification', 'birth_place') }}) as birth_place,
        coalesce(public.try_date(f.tanggal_lahir), {{ ke_tanggal(ab('employee_identification', 'dt_birth')) }}) as dt_birth,
        {{ ke_tanggal(ab('employee_identification', 'dt_start_work')) }}         as dt_start_work,
        {{ ke_tanggal(ab('employee_identification', 'dt_retirement')) }}         as dt_retirement,
        coalesce(public.try_date(f.tmt_karyawan), {{ ke_tanggal(ab('employee_identification', 'dt_appointed_employee')) }}) as dt_appointed_employee,
        coalesce({{ ke_tanggal(ab('employee_identification', 'dt_grade_start')) }}, t.dt_position_start) as dt_grade_start,
        {{ baku('angkasabiru', 'employment_type', ab('employee_identification', 'employment_type')) }} as employment_type,
        t.job_class                                                              as job_class,
        {{ baku('angkasabiru', 'gender', ab('employee_identification', 'gender')) }} as gender,
        {{ ke_ponsel(ab('employee_identification', ['mobile_phone', 'home_phone'])) }} as mobile_phone,
        lower({{ ab('employee_identification', 'corporate_email') }}) as corporate_email,
        {{ kolom_teknis('angkasabiru') }},
        r._row_hash
    from {{ source('raw_ab', 'employee_identification') }} r
    left join {{ ref('int_posisi_terkini_angkasabiru') }} t
           on t.new_nip = {{ ab('employee_identification', 'id_employee') }}
    left join (
        select distinct on (nullif(btrim(new_nip), ''))
               nullif(btrim(new_nip), '') as new_nip, tanggal_lahir, tmt_karyawan
        from {{ source('ref_ab', 'tmt_karyawan_angkasabiru') }}
        order by nullif(btrim(new_nip), '')
    ) f on f.new_nip = {{ ab('employee_identification', 'id_employee') }}
) x
where id_employee is not null
order by id_employee, _row_hash

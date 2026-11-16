{#
  Mapping Angkasa Biru Retail: employee_family_member <- spouses + childrens (dua endpoint lama digabung).
    id_employee <- nik (NIP lama pegawai) -> kunci pegawai DWH;  id_family_member <- id;  full_name <- nama;
    gender <- jns_kelamin;  birth_place <- tmp_lahir (kosong di API);  dt_birth <- tgl_lahir.
    relationship_type = DWH Generate: 'Pasangan' untuk baris spouses, 'Anak' untuk baris childrens.
  id_type tidak punya sumber -> NULL.
#}
    select
        {{ id_employee('angkasabiruretail', nip7(abr('spouses', 'nik'))) }} as id_employee,
        {{ abr('spouses', 'id') }}          as id_family_member,
        upper({{ abr('spouses', 'nama') }}) as full_name,
        cast('Pasangan' as text) as relationship_type,
        {{ baku('angkasabiruretail', 'gender', abr('spouses', 'jns_kelamin')) }} as gender,
        upper({{ abr('spouses', 'tmp_lahir') }}) as birth_place,
        {{ ke_tanggal(abr('spouses', 'tgl_lahir')) }} as dt_birth,
        cast(null as text)    as id_type,
        {{ kolom_teknis('angkasabiruretail') }}
    from {{ source('raw_abr', 'spouses') }} r
    where {{ abr('spouses', 'id') }} is not null
union all
    select
        {{ id_employee('angkasabiruretail', nip7(abr('childrens', 'nik'))) }} as id_employee,
        {{ abr('childrens', 'id') }}          as id_family_member,
        upper({{ abr('childrens', 'nama') }}) as full_name,
        cast('Anak' as text) as relationship_type,
        {{ baku('angkasabiruretail', 'gender', abr('childrens', 'jns_kelamin')) }} as gender,
        upper({{ abr('childrens', 'tmp_lahir') }}) as birth_place,
        {{ ke_tanggal(abr('childrens', 'tgl_lahir')) }} as dt_birth,
        cast(null as text)    as id_type,
        {{ kolom_teknis('angkasabiruretail') }}
    from {{ source('raw_abr', 'childrens') }} r
    where {{ abr('childrens', 'id') }} is not null

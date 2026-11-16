{#
  Mapping AB: org_unit <- units (id_org_unit, org_unit_name, id_parent_org_unit).
  org_level dihitung dengan penalaran hirarki: unit yang id_org_unit = id_parent_org_unit adalah puncak
  (level 1), anaknya level 2, cucunya level 3, dan seterusnya. Unit yang induknya tidak ada di daftar
  (tidak tersambung ke puncak mana pun) tidak bisa dinalar levelnya -> NULL.
  id_org_unit kembar di sumber disatukan (PK): diutamakan baris puncak, lalu nama terkecil secara abjad.
  fk_id_company tidak ada di mapping maupun di raw -> diisi perusahaan Angkasa Biru (DWH Generate).
#}
with recursive src as (
    select distinct on (id_org_unit) *
    from (
        select
            {{ ab('units', 'id_org_unit') }}        as id_org_unit,
            {{ ab('units', 'org_unit_name') }}      as org_unit_name,
            {{ ab('units', 'id_parent_org_unit') }} as id_parent_org_unit,
            r._batch_id, r._extracted_at
        from {{ source('raw_ab', 'units') }} r
    ) u
    where id_org_unit is not null
    order by id_org_unit, (id_org_unit = id_parent_org_unit) desc, org_unit_name
),
hirarki as (
    select id_org_unit, 1 as org_level from src where id_org_unit = id_parent_org_unit
    union all
    select c.id_org_unit, h.org_level + 1
    from src c
    join hirarki h on c.id_parent_org_unit = h.id_org_unit
    where c.id_org_unit <> c.id_parent_org_unit and h.org_level < 20
),
level_unit as (
    select id_org_unit, min(org_level) as org_level from hirarki group by 1
)
select
    r.id_org_unit,
    r.org_unit_name,
    l.org_level,
    r.id_parent_org_unit,
    (select id_company from {{ ref('ref_company_angkasabiru') }} where source_system = 'angkasabiru') as fk_id_company,
    {{ kolom_teknis('angkasabiru') }}
from src r
left join level_unit l using (id_org_unit)

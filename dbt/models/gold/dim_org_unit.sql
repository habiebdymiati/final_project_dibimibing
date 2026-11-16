{#
  org_hierarchy_path: nama unit dari puncak sampai unit ini, dipisah " > ".
  Puncak = unit tanpa induk, unit yang induknya dirinya sendiri, atau unit yang induknya tidak ada di daftar.
  Unit yang terjebak di lingkaran induk-anak tetap dimuat, dengan jalur berisi namanya sendiri.
#}
with recursive src as (
    select kode_sumber || '-' || id_org_unit as org_unit_key,
           kode_sumber || '-' || id_parent_org_unit as parent_key,
           id_org_unit, org_unit_name, org_level
    from ({{ dari_silver('org_unit', 'id_org_unit, id_parent_org_unit, org_unit_name, org_level') }}) u
),
tree as (
    select s.org_unit_key, s.org_unit_name as org_hierarchy_path, array[s.org_unit_key] as dilalui
    from src s
    where s.parent_key is null or s.parent_key = s.org_unit_key
       or not exists (select 1 from src p where p.org_unit_key = s.parent_key)
    union all
    select c.org_unit_key, t.org_hierarchy_path || ' > ' || c.org_unit_name, t.dilalui || c.org_unit_key
    from src c
    join tree t on c.parent_key = t.org_unit_key
    where c.parent_key <> c.org_unit_key and not (c.org_unit_key = any (t.dilalui))
)
select s.org_unit_key, s.id_org_unit as org_unit_id, s.org_unit_name,
       coalesce(t.org_hierarchy_path, s.org_unit_name) as org_hierarchy_path, s.org_level
from src s
left join tree t on t.org_unit_key = s.org_unit_key
union all
select 'UNKNOWN', 'UNKNOWN', 'Tidak diketahui', 'Tidak diketahui', null

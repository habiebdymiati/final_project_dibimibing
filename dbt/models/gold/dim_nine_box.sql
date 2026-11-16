{#
  Dimensi kisi 9-Box, mengikuti acuan kisi Rinjani (gambar acuan 15 November 2026):
  sumbu mendatar = performance (Low -> High), sumbu tegak = capacity/potential (Low -> High).

        capacity High   | 4. Sleeping Tiger | 7. Promotable        | 9. High Potential
        capacity Medium | 2. Sleeping Tiger | 5. Promotable        | 8. Promotable
        capacity Low    | 1. Unfit          | 3. Solid Contributor | 6. Solid Contributor
                          perf Low            perf Medium            perf High

  nine_box_key mengikuti nomor sel pada acuan; 0 = Unclassified untuk pegawai tanpa data kedua sumbu.
#}
select *
from (values
    (0, 'Unclassified',      'Unknown', 'Unknown', 'Unclassified'),
    (1, 'Unfit',             'Low',     'Low',     'Unfit'),
    (2, 'Sleeping Tiger',    'Low',     'Medium',  'Sleeping Tiger'),
    (3, 'Solid Contributor', 'Medium',  'Low',     'Solid Contributor'),
    (4, 'Sleeping Tiger',    'Low',     'High',    'Sleeping Tiger'),
    (5, 'Promotable',        'Medium',  'Medium',  'Promotable'),
    (6, 'Solid Contributor', 'High',    'Low',     'Solid Contributor'),
    (7, 'Promotable',        'Medium',  'High',    'Promotable'),
    (8, 'Promotable',        'High',    'Medium',  'Promotable'),
    (9, 'High Potential',    'High',    'High',    'High Potential')
) as t(nine_box_key, nine_box_label, performance_level, capacity_level, talent_cluster)

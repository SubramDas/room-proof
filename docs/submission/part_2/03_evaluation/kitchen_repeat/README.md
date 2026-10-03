# Kitchen repeat capture comparison

same kitchen and laser dimensions confirmed by operator.

Two distinct raw video hashes are preserved. Sorted room extents are proxies; no complete per-wall repeatability pass is claimed. Limits use max(1 cm, 0.5% of the first measurement); repeated height uses 1 cm.

| Measurement | First m | New m | Difference cm | Limit cm | Proxy outcome |
|---|---:|---:|---:|---:|---|
| short_extent | 2.3770 | 2.3730 | 0.40 | 1.19 | within limit |
| long_extent | 2.4954 | 2.3865 | 10.89 | 1.25 | FAIL |
| ceiling_height | 2.7921 | 2.7611 | 3.10 | 1.00 | FAIL |

The longer extent and ceiling height vary beyond their limits. Physical wall correspondence is still needed for the full wall repeatability gate. Inspect both provenance files: saved-run differences are not a controlled same-source repeatability experiment.

Against the confirmed 2.80 m laser height, the new estimate is 3.89 cm low, outside the 1.5 cm height gate. The 3.10 cm between-run height spread also exceeds 1 cm. This is evidence of both error and variation in these outputs; it does not isolate the cause.

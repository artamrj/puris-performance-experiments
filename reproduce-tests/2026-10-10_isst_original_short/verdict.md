# Result – 2026-10-10_1118_original_short

Machine: Intel(R) Xeon(R) Silver 4314 CPU @ 2.40GHz · 24 vCPU · 46.13 GiB · single-core score 1682815

> **Short test (2-min stages):** checks that the pipeline works. The numbers are not comparable with the reference or the thesis – with short stages no backlog builds up in time.

| Configuration | valid runs | tipping stage (median, range) | capacity | tx/s per core | recovery | restarts after warm-up | comparison |
|---|---|---|---|---|---|---|---|
| original-k0 | 1 of 1 | 0.2/s (0.2/s – 0.2/s) | – | – | 0 of 1 | 1 | not compared (short test) |
| original-k1 | 1 of 1 | 4/s (4/s – 4/s) | 3/s | 2.00 | 0 of 1 | 2 | not compared (short test) |

Saturation criterion (as in the thesis): a stage is saturated when fewer than 95 % of its planned transactions are completed;
the tipping stage is the first saturated stage after the warm-up. Further readings in summary.json: `relaxed` (or > 1 % failed),
`strict` (or ≥ 1 "Invalidating …"). References: reference/<configuration>.json (main measurement on the NAS).
Restarts after warm-up: containers of the system under test restarted after the warm-up, per valid run – a result, the run stays valid.

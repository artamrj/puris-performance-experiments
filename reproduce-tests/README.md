# reproduce-tests

Result folders of **short tests** of `reproduce` (`REPRODUCE_SMOKE=1`: 2-min stages, 1 run per configuration).
They only check that the pipeline works. **Not results of the thesis, never copied into `runs/`.**
Full runs of `reproduce` go into `runs/` (folders `<date>_<time>_<configuration>_rep-<n>`).

| Folder | Machine | Profile | Commit | Lab book |
|---|---|---|---|---|
| `2026-10-10_isst_original_short/` | VM of the supervisor (Fraunhofer ISST), Xeon Silver 4314, 24 vCPU, 46 GiB | `original` (`original-k0`, `original-k1`) | `317813d` | `LABORBUCH.md`, 2026-10-10 |

Copied unchanged from `~/puris/puris-repro/results/<folder>/` on the VM (`rsync -a`); `SHA256SUMS` checked on the VM and on the Mac.

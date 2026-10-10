# Screenshots of `reproduce`

The images in this folder are terminal output of `reproduce` (version of 2026-10-10), converted from ANSI colours to SVG. They were not drawn by hand. The commit `6c1b7aa` in the header is the repository state that the rebuild test measured with.

| File | Content | Source |
|---|---|---|
| `reproduce-dashboard-measure.svg` | Dashboard during run 1 of `compact-k1`, load stage s9 (1.5/s) | real log of the rebuild test, cut at 02:38:51 UTC (2026-10-10) |
| `reproduce-dashboard-deploy.svg` | Dashboard during `deploy`, component 11 of 11 | real log of the rebuild test, cut at 21:32:20 UTC (2026-10-09) |
| `reproduce-dashboard-pods.svg` | Pods view (key `p`) | live cluster after the rebuild test (idle) |
| `reproduce-status.svg` | `./reproduce status` after the rebuild test | real state folder |
| `reproduce-watch.svg` | `./reproduce watch`, end of the rebuild test | real log, 02:53:59–03:28:25 UTC |
| `reproduce-help.svg`, `reproduce-typo.svg` | `./reproduce help` and a mistyped command | script output |

**How the dashboard frames were made.** [`tools/screenshots.py`](../../tools/screenshots.py) copies the log of the rebuild test (NAS VM, 2026-10-09/10) up to the chosen moment into a scratch folder. It shifts the log's clock so that this moment is "now", and recreates the run folders and markers as they were at that moment. Then it runs `./reproduce dashboard --once`. Two messages of the old log are shown in the current message format with the same values: steal time as a percentage, and the log capacity probe as a sentence instead of JSON. Paths under the home directory are written as `/home/user/`. In the deploy frame, the *Cluster* panel shows the live cluster at capture time.

**Regenerate** (on the server, then locally):

```bash
REPRODUCE_HOME=~/puris-repro python3 tools/screenshots.py ./reproduce /tmp/shots
python3 tools/ansi2svg.py /tmp/shots/status.ans docs/img/reproduce-status.svg --title "./reproduce status" --cmd "./reproduce status" --cols 104
```

[`tools/ansi2svg.py`](../../tools/ansi2svg.py) needs only the Python standard library. Every text run sits at its terminal column, so boxes stay aligned in any monospace font.

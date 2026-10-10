#!/usr/bin/env python3
"""Captures the terminal screenshots in docs/img/ from a real `reproduce` home (run on the server).

The dashboard frames replay the real log of the rebuild test on the NAS VM (2026-10-09/10) into
scratch homes: the log is cut at a chosen moment and its clock is shifted so that this moment is
"now"; run folders and markers are recreated as they were at that moment (meta.json of the finished
K0 run is copied). Two old messages are shown in the current message format (same values). The
pods view, status and help come from the real home and the live cluster. Paths under the home
directory are written as /home/user/. Render afterwards with tools/ansi2svg.py (docs/img/README.md).

  REPRODUCE_HOME=~/repro-test/puris-repro python3 tools/screenshots.py ./reproduce /tmp/shots
"""
import os, re, subprocess, sys, time, shutil

L = os.path.abspath(os.path.expanduser(os.environ.get("REPRODUCE_HOME", "~/puris-repro")))
SCR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else "./reproduce"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/shots"
RES = L + "/results/2026-10-09_2158_compact"
os.makedirs(OUT, exist_ok=True)
lines = open(L + "/state/logs/reproduce.log", encoding="utf-8").read().splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("20:44:"))
lines = lines[start:]
# two messages of the old log in the current message format (same values; reproduce prints them like this since 2026-10-10)
import json
def modern(l):
    m = re.match(r"^(.* machine busy \(steal )([0-9.]+)( ≥ 1 %\).*)$", l)
    if m: return m.group(1) + "%.1f %%" % (float(m.group(2)) * 100) + m.group(3)
    m = re.match(r"^(.* log capacity probe passed: )(\{.*\})$", l)
    if m:
        p = json.loads(m.group(2))
        return m.group(1) + "%d of %d transactions in Loki, %d failed, %g discarded" % (p["triggers_in_loki"], p["requests"], p["requests_failed"], p["loki_discarded"])
    return l
lines = [modern(l) for l in lines]
T = re.compile(r"^(\d\d):(\d\d):(\d\d)( .*)$")


def sod(h, m, s):
    return int(h) * 3600 + int(m) * 60 + int(s)


def A(hms, day=0):
    return sod(*hms.split(":")) + day * 86400


absl, day, prev = [], 0, None
for l in lines:
    m = T.match(l)
    if not m:
        absl.append(None); continue
    t = sod(*m.group(1, 2, 3))
    if prev is not None and t < prev - 43200: day += 1
    prev = t; absl.append(t + day * 86400)


def run(name, args, home, extra=None, cols=104):
    env = dict(os.environ, REPRODUCE_HOME=home, FORCE_COLOR="1", COLUMNS=str(cols), LINES="40", TZ="UTC")
    env.update(extra or {})
    out = subprocess.run(["bash", SCR] + args, env=env, capture_output=True, text=True)
    open(OUT + "/" + name + ".ans", "w").write((out.stdout + out.stderr).replace(os.path.expanduser("~") + "/", "/home/user/"))
    print(name, len((out.stdout + out.stderr).splitlines()), "lines")


def scene(name, cut, phase, files, since, runs=(), kube=True):
    w = "/tmp/shot-" + name
    shutil.rmtree(w, ignore_errors=True)
    os.makedirs(w + "/state/logs"); os.makedirs(w + "/state/markers")
    for d in ("src", "tools"): os.symlink(L + "/" + d, w + "/" + d)
    shutil.copy(L + "/state/profile", w + "/state/profile")
    if kube: shutil.copy(L + "/state/kubeconfig", w + "/state/kubeconfig")
    off = time.time() - cut                     # epoch = off + absolute log second
    ep = lambda a: off + a
    keep = []
    for l, a in zip(lines, absl):
        if a is not None and a > cut: break
        keep.append(l if a is None else time.strftime("%H:%M:%S", time.gmtime(ep(a))) + T.match(l).group(4))
    open(w + "/state/logs/reproduce.log", "w", encoding="utf-8").write("\n".join(keep) + "\n")
    for f, v in files.items():
        os.makedirs(os.path.dirname(w + "/state/" + f), exist_ok=True); open(w + "/state/" + f, "w").write(v)
    if runs:
        rd = w + "/state/results/" + time.strftime("%Y-%m-%d_%H%M", time.gmtime(ep(A("21:58:21")))) + "_compact"
        os.makedirs(rd)
        for f, v in ((".mode", "full"), (".reps", "1"), (".commit", "x"), (".profile", "compact")): open(rd + "/" + f, "w").write(v + "\n")
        open(w + "/state/results-current", "w").write(rd + "\n")
        for cfg, a, meta in runs:
            rn = rd + "/" + time.strftime("%Y-%m-%d_%H%M", time.gmtime(ep(a))) + "_%s_rep-1" % cfg
            os.makedirs(rn)
            if meta: shutil.copy(meta, rn + "/meta.json")
            else: open(w + "/state/markers/run", "w").write(rn + "\n")
    sl = subprocess.Popen(["setsid", "sleep", "120"])
    open(w + "/state/job", "w").write("pid=%d command=_continue phase=%s started=%s since=%d mode=full reps=1\n" % (
        sl.pid, phase, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ep(A("20:44:43")))), int(ep(since))))
    run(name, ["dashboard", "--once", "main"], w)
    sl.kill(); shutil.rmtree(w)


# 1 deploy: [11/11] k6 operator is starting
scene("dashboard-deploy", A("21:32:20"), "deploy", {}, A("20:49:05"))
# 2 measure: K1 run, stage s9 (1.5/s), K0 already valid; measurement-safe → no kubectl
scene("dashboard-measure", A("02:38:51", 1), "measure:compact-k1", {"config": "compact-k1\n", "verified": "x\n", "s0/SHA256SUMS": "x\n"}, A("21:58:21"),
      runs=(("compact-k0", A("22:10:11"), RES + "/2026-10-09_2210_compact-k0_rep-1/meta.json"), ("compact-k1", A("00:40:47", 1), None)), kube=False)
# 3 pods view, live cluster (idle after the rebuild test)
run("dashboard-pods", ["dashboard", "--once", "pods"], L, cols=118)
# 4 status of the finished rebuild test
run("status", ["status"], L)
# 5 help and a typo
run("help", ["help"], L)
run("typo", ["deplyo"], L)
# 6 line output (what `watch` prints) – end of the rebuild test, coloured by the script's own paint()
seg = [l for l, a in zip(lines, absl) if a is not None and A("02:53:59", 1) <= a]
body = open(SCR, encoding="utf-8").read()
paint = body[body.index("paint() {"):body.index("\n}\n", body.index("paint() {")) + 3]
sh = "C_OK=$'\\033[32m' C_WARN=$'\\033[33m' C_ERR=$'\\033[1;31m' C_RUN=$'\\033[36m' C_DIM=$'\\033[2m' C_B=$'\\033[1m' C_0=$'\\033[0m'\n" + paint + \
     'while IFS= read -r l; do paint "$l"; done\n'
open("/tmp/paint.sh", "w").write(sh)
out = subprocess.run(["bash", "/tmp/paint.sh"], input="\n".join(seg) + "\n", capture_output=True, text=True)
open(OUT + "/watch.ans", "w").write((out.stdout + out.stderr).replace(os.path.expanduser("~") + "/", "/home/user/"))
print("watch", len(seg), "lines")

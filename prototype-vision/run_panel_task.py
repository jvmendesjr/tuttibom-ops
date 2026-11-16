#!/usr/bin/env python3
"""Scripted panel task: locate -> click -> verify focus, one step at a time.
Step 1: email field. Step 2: password field. No typing, no submit.
Aborts on locate failure or failed verification."""
import json
import os
import subprocess
import sys

sys.path.insert(0, ".")
from jev_navigate import locate, prep  # noqa: E402

URL = "https://deskcomm.petemcasa.com/login"
ENV = dict(os.environ, NODE_PATH="/home/pc/.local/opt/node22/lib/node_modules")


def click(x, y):
    out = subprocess.run(
        ["node", "panel_driver.cjs", "click", URL, str(x), str(y)],
        capture_output=True, text=True, env=ENV)
    return json.loads(out.stdout)


def main():
    png = open("/tmp/panel-task.png", "rb").read()
    _, w, h = prep(png)
    steps = [("campo de e-mail", "email"), ("campo de senha", "password")]
    ok = True
    for target, expect in steps:
        loc, rec = locate(png, target, w, h)
        print("step:", target, "->", loc)
        if not loc:
            print("ABORT: locate failed")
            ok = False
            break
        r = click(loc["x"], loc["y"])
        a = r.get("active")
        verified = bool(a and a.get("id") == expect)
        print("  click", (loc["x"], loc["y"]), "-> activeElement:", a,
              "->", "VERIFIED" if verified else "NOT VERIFIED")
        if not verified:
            ok = False
            break
    print("TASK:", "SUCCESS 2/2 steps verified" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

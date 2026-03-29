#!/usr/bin/env python3 -B
import sys
from pathlib import Path
from scan import *

EG = Path.home() / "gits/moot/optimize/misc/auto93.csv"

def csv(f=EG): 
  return open(f).read() if Path(f).exists() else ""

def test_o():
  t = o(a=1, b=2); t.c = 3
  assert t.a == 1 and t["b"] == 2 and t.c == 3

def test_clean_isnum():
  assert isnum("3.14") and not isnum("a")
  assert clean(" NA ") == "?" and clean(" a ") == "a"

def test_prep():
  m = prep(csv())
  assert m.nc > 0 and len(m.rows) > 10 and len(m.hdr) == m.nc

def test_cols():
  m = prep(csv())
  assert m.xs and m.ys and set(m.xs).isdisjoint(m.ys)

def test_numstat():
  st = numstat([10, 20, 30, 40, 50])
  assert st.mu == 30.0 and st.sd > 0

def test_symstat():
  st = symstat(["a", "a", "b", "c"])
  assert st.n == 4 and st.ent > 0

def test_dist():
  m = prep(csv())
  assert 0 <= dists(m.rows[0], m.rows[1], m) <= 1

def test_yscore():
  m = prep(csv())
  assert 0 <= yscore(m.rows[0], m) <= 1

def test_cluster():
  m = prep(csv())
  res = half(m.rows, m)
  assert len(res[0]) + len(res[1]) == len(m.rows)

def test_tree():
  m = prep(csv())
  random.shuffle(m.rows)
  print("\nTree:"); tshow(grow(m.rows[:50], m), m)

def test_acquire():
  res = learn(csv(), rounds=2, labels=5)
  assert len(res.log) == 5 and res.summary

def cli():
  args = sys.argv[1:]
  tests = {k: v for k, v in globals().items() if k.startswith("test_")}
  if "-h" in args or "--help" in args:
    print("Usage: scaneg.py [--all] [--test_name]")
    return [print(f"  --{k[5:]}") for k in tests]
  for k, fn in tests.items():
    random.seed(1)
    if "--all" in args or not args or f"--{k[5:]}" in args:
      try: fn(); print(f"✅ {k}")
      except Exception as e: print(f"❌ {k}: {e}")

if __name__ == "__main__": cli()

#!/usr/bin/env python3 -B
# scan.py — geometry-based active learning + decision tree
import sys, re, math, random
from pathlib import Path

class o(dict):
  __getattr__ = dict.__getitem__; __setattr__ = dict.__setitem__

# Removed clustering configs, kept core tree/peeks vars
the = o(seed=42, stop=4, labels=10, check=5, w=32, eps=1e-32)

EG = Path.home() / "gits/moot/optimize/misc/auto93.csv"
def csv(f=str(EG)): return open(f).read() if Path(f).exists() else ""

# ---- lib ----
def isnum(x):
  try: float(x); return True
  except: return False

def thing(x):
  if str(x).lower() in ["true", "t"]: return True
  if str(x).lower() in ["false", "f"]: return False
  try: return int(x)
  except:
    try: return float(x)
    except: return str(x).strip()

def norm(v, lo, hi): return (v-lo) / (hi-lo+the.eps)

def clean(v):
  v = str(v).strip()
  return "?" if not v or re.match(r"^[Nn][Aa]$", v) else v

# ---- distance ----
def distVal(a, b, c):
  n = lambda v: norm(float(v), c.lo, c.hi)
  if a=="?": return max(n(b), 1-n(b))
  if b=="?": return max(n(a), 1-n(a))
  return (n(a)-n(b))**2

def dist(a, b, k, m):
  c = m.col[k]
  if not c: return 0 if a==b else 1
  if a=="?" and b=="?": return 1
  return distVal(a, b, c)

def dists(r1, r2, m):
  ds = [dist(r1[k], r2[k], k, m) for k in range(m.nc)
        if not(r1[k]=="?" and r2[k]=="?")]
  return math.sqrt(sum(ds)/len(ds)) if ds else 1

# ---- prep / data ----
def dataBounds(rows):
  lo, hi = {}, {}
  for r in rows:
    for k, v in enumerate(r):
      if isnum(v):
        lo[k] = min(lo.get(k, float(v)), float(v))
        hi[k] = max(hi.get(k, float(v)), float(v))
  return lo, hi

def dataCol(k, h, lo, hi):
  if k not in lo: return None
  heaven = 0 if h[-1:]=="-" else (1 if h[-1:]=="+" else None)
  return o(lo=lo[k], hi=hi[k], heaven=heaven)

def dataCoerce(rows, col):
  out = [[float(v) if col[k] and v!="?" else v 
          for k,v in enumerate(r)] for r in rows]
  random.seed(the.seed); random.shuffle(out)
  return out

def prep(csv_str):
  lines = csv_str.strip().split("\n")
  hdr   = [h.strip() for h in lines[0].split(",")]; nc = len(hdr)
  rows  = [[clean(v) for v in l.split(",")] for l in lines[1:]]
  lo,hi = dataBounds(rows)
  col   = [dataCol(k, hdr[k], lo, hi) for k in range(nc)]
  xs    = [k for k in range(nc) if not(col[k] and col[k].heaven is not None)]
  ys    = [k for k in range(nc) if     col[k] and col[k].heaven is not None]
  return o(hdr=hdr, nc=nc, col=col, xs=xs, ys=ys, rows=dataCoerce(rows, col))

# ---- score ----
def yscore(row, m):
  ds = [(norm(row[k], m.col[k].lo, m.col[k].hi) - m.col[k].heaven)**2
        for k in m.ys]
  return math.sqrt(sum(ds)/len(ds)) if ds else 0

def wins(rows, m):
  scores = [yscore(r, m) for r in rows]
  lo = min(scores) if scores else 0
  mu = statMean(scores)
  return lambda r: int(100 * (1 - (yscore(r, m) - lo) / (mu - lo + the.eps)))

# ---- stats ----
def statVals(rows, k): 
  return [r[k] for r in rows if r[k]!="?"]

def statMean(a): 
  return sum(a)/len(a) if a else 0

def statSd(a):
  if len(a)<2: return 0
  mu = statMean(a)
  return math.sqrt(sum((v-mu)**2 for v in a)/(len(a)-1))

def statMode(a): 
  return max(set(a), key=a.count) if a else None

# ---- acquire (peeks style) ----
def acqLearn(rows, m, oracle=None):
  unlab = rows[:]
  random.shuffle(unlab)
  unlab = unlab[:128] 
  known = [unlab.pop(0)]
  for _ in range(the.check - 1):
    if not unlab: break
    best_idx = max(range(len(unlab)), 
                   key=lambda u: min(dists(unlab[u], k, m) for k in known))
    known.append(unlab.pop(best_idx))
  known.sort(key=lambda r: (oracle or yscore)(r, m))
  def score(u):
    return sum(dists(unlab[u], known[i], m) / (i + 1) for i in range(len(known)))
  for _ in range(the.labels - the.check):
    if not unlab: break
    best_idx = min(range(len(unlab)), key=score)
    known.append(unlab.pop(best_idx))
    known.sort(key=lambda r: (oracle or yscore)(r, m))
  log = [o(label=i+1, row=r, score=(oracle or yscore)(r, m)) 
         for i, r in enumerate(known[:the.labels])]
  return o(log=log)

# ---- tree ----
def treeVal(k, top, bot, m):
  a = statVals(top, k)
  if m.col[k]:
    b = statVals(bot, k)
    return (statMean(a)+statMean(b))/2 if a and b else None
  return statMode(a)

def treePart(rows, k, v, m):
  L, R = [], []
  for r in rows:
    if r[k] != "?" and (r[k]<=v if m.col[k] else r[k]==v): L.append(r)
    else: R.append(r)
  return L, R

def treeWeight(l, r, m):
  yl = [yscore(x, m) for x in l]; yr = [yscore(x, m) for x in r]
  return statSd(yl)*len(l) + statSd(yr)*len(r)

def treeBestCol(rows, m, top, bot):
  bv, bk, bval = 1/the.eps, None, None
  for k in m.xs:
    v = treeVal(k, top, bot, m)
    if v is None: continue
    l, r = treePart(rows, k, v, m)
    if not l or not r: continue
    if (w := treeWeight(l, r, m)) < bv: bv, bk, bval = w, k, v
  return bk, bval

def treeKids(node, rows, bk, bval, m):
  l, r = treePart(rows, bk, bval, m)
  h = m.hdr[bk]; f = f"{bval:.2f}" if m.col[bk] else str(bval)
  s1, s2 = ((f"{h}<={f}", f"{h}> {f}") if m.col[bk] else (f"{h}=={f}", f"{h}!={f}"))
  node.cut = (bk, bval)
  node.kids = [treeGrow(l, m, s1), treeGrow(r, m, s2)]

def treeGrow(rows, m, pre=""):
  node = o(rows=rows, pre=pre, kids=[])
  if len(rows) > the.stop * 2:
    rs = sorted(rows, key=lambda r: yscore(r, m))
    bk, bval = treeBestCol(rows, m, rs[:len(rs)//2], rs[len(rs)//2:])
    if bk is not None: treeKids(node, rows, bk, bval, m)
  return node

def treeLeaf(node, row, m):
  if not node.kids: return node
  k, v = node.cut
  ok = row[k]!="?" and (row[k]<=v if m.col[k] else row[k]==v)
  return treeLeaf(node.kids[0 if ok else 1], row, m)

def treeShow(node, m, lvl=0):
  lbl = ('|  '*(lvl-1) if lvl else '')+node.pre
  if not node.kids:
    mu = statMean([yscore(r, m) for r in node.rows])
    print(f"{lbl:<{the.w}} n={len(node.rows):3d}  y={mu:.2f}")
  else:
    if lbl: print(lbl)
    for kid in node.kids: treeShow(kid, m, lvl+1)

# ---- tests ----
def tests(*ignore):
  for k, fn in list(globals().items()):
    if k.startswith("test_") and k not in ignore:
       yield k,fn
   
def test_all():
  for k, fn in tests("test_all", "test_h", "test_help"):
    print(f"? {k} :",end="")
    random.seed(the.seed)
    try: fn(); print(f"✅ PASS")
    except Exception as e: print(f"❌ FAIL: {e}")

def test_h():
  print("Usage: scan.py [--all] [--test_name] [args...]")
  for k, fn in tests():
     print(f"  --{k[5:]:10} {' '.join(fn.__annotations__)}") 

test_help = test_h

def test_o():
  t = o(a=1, b=2); t.c = 3
  assert t.a == 1 and t["b"] == 2 and t.c == 3

def test_clean_isnum():
  assert isnum("3.14") and not isnum("a")
  assert clean(" NA ") == "?" and clean(" a ") == "a"
  assert thing("true") is True and thing("42") == 42

def test_prep(file: str = str(EG)):
  m = prep(csv(file))
  assert m.nc > 0 and len(m.rows) > 10 and len(m.hdr) == m.nc

def test_cols(file: str = str(EG)):
  m = prep(csv(file))
  assert m.xs and m.ys and set(m.xs).isdisjoint(m.ys)

def test_dist(file: str = str(EG)):
  m = prep(csv(file))
  assert 0 <= dists(m.rows[0], m.rows[1], m) <= 1

def test_yscore(file: str = str(EG)):
  m = prep(csv(file))
  assert 0 <= yscore(m.rows[0], m) <= 1

def test_tree(file: str = str(EG)):
  m = prep(csv(file))
  print("\nTree:"); treeShow(treeGrow(m.rows[:50], m), m)

def test_acquire(file: str = str(EG)):
  m = prep(csv(file))
  n = len(m.rows) // 2
  random.shuffle(m.rows)
  train, test = m.rows[:n], m.rows[n:][:500]
  score_win = wins(m.rows, m) 
  res = acqLearn(train, m)
  t = treeGrow([x.row for x in res.log], m)
  def pred(r):
    nd = treeLeaf(t, r, m)
    return statMean([yscore(x, m) for x in nd.rows])
  guess = sorted(test, key=pred)
  best_row = guess[0]
  print(score_win(best_row))
 
# ---- cli ----
def cli():
  args = sys.argv[1:]
  if not args: return test_all()
  while args:
    random.seed(the.seed)
    k = args.pop(0).lstrip("-")
    if fn := globals().get(f"test_{k}"):
      fargs = [thing(args.pop(0)) for _ in fn.__annotations__ if args]
      fn(*fargs)
    elif k in the: the[k] = thing(args.pop(0))
    else: print(f"Unknown option: {k}")

if __name__ == "__main__": cli()

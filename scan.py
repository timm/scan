"""
scan.py — geometry-based active learning + decision tree

  m        : o(hdr,nc,col,xs,ys,rows)
    hdr    : [str]                  column names
    nc     : int                    number of columns
    col    : [None|o(lo,hi,heaven)] None=sym; heaven=None → num; 0|1 → y
    xs     : [int]                  x-col indices (not y)
    ys     : [int]                  y-col indices
    rows   : [[val]]                shuffled, coerced rows

  node : o(rows,pre,kids,cut?)   cut=(k,v) split on col k at value v
  row  : [val]                   val is float|str|"?"
"""
import re, math, random

class o(dict):
  __getattr__ = dict.__getitem__; __setattr__ = dict.__setitem__

# ---- lib ----
def isnum(x):
  try: float(x); return True
  except: return False

def norm(v,lo,hi): return (v-lo)/(hi-lo+1e-32)

def clean(v):
  v = v.strip()
  return "?" if not v or re.match(r"^[Nn][Aa]$",v) else v

def dist(a,b,k,m):
  c = m.col[k]
  if not c: return 0 if a==b else 1
  if a=="?" and b=="?": return 1
  n = lambda v: norm(float(v), c.lo, c.hi)
  if a=="?": v = n(b); return max(v,1-v)
  if b=="?": v = n(a); return max(v,1-v)
  return (n(a)-n(b))**2

def dists(r1,r2,m):
  ds = [dist(r1[k],r2[k],k,m) for k in range(m.nc)
        if not(r1[k]=="?" and r2[k]=="?")]
  return math.sqrt(sum(ds)/len(ds)) if ds else 1

# ---- prep ----
def prep(csv,seed=42):
  lines = csv.strip().split("\n")
  hdr = [h.strip() for h in lines[0].split(",")]; nc = len(hdr)
  lo,hi = {},{}
  rows = [[clean(v) for v in l.split(",")] for l in lines[1:]]
  for r in rows:
    for k,v in enumerate(r):
      if not isnum(v): continue
      lo[k] = min(lo.get(k,float(v)),float(v))
      hi[k] = max(hi.get(k,float(v)),float(v))
  heaven = {k:(0 if h[-1:]=="-" else 1)
            for k,h in enumerate(hdr) if h[-1:] in ("-","+")}
  col = [None if k not in lo else o(lo=lo[k], hi=hi[k], heaven=heaven.get(k))
         for k in range(nc)]
  xs = [k for k in range(nc) if not(col[k] and col[k].heaven is not None)]
  ys = [k for k in range(nc) if     col[k] and col[k].heaven is not None]
  coerced = [[float(v) if col[k] and v!="?" else v
              for k,v in enumerate(r)] for r in rows]
  random.seed(seed)
  random.shuffle(coerced)
  return o(hdr=hdr, nc=nc, col=col, xs=xs, ys=ys, rows=coerced)

# ---- score ----
def yscore(row,m):
  ds = [(norm(row[k], m.col[k].lo, m.col[k].hi) - m.col[k].heaven)**2
        for k in m.ys]
  return math.sqrt(sum(ds)/len(ds)) if ds else 0

# ---- half ----
def poles(rows,m):
  s = rows[:20]; best = -1; ai,bi = 0,1
  for i,a in enumerate(s):
    for j,b in enumerate(s[i+1:],i+1):
      if (d:=dists(a,b,m)) > best:
        best,ai,bi = d,i,j
  return (bi,ai) if yscore(rows[ai],m) > yscore(rows[bi],m) else (ai,bi)

def far(cluster,m):
  rows = list(cluster); ai,bi = poles(rows,m)
  a = rows.pop(ai); b = rows.pop(bi-1 if bi>ai else bi)
  return [a,b]+rows

def half(cluster,m):
  a,b,*rest = cluster; A,B = [a],[b]
  for r in rest:
    (A if dists(r,a,m)<=dists(r,b,m) else B).append(r)
  return [A,B]

def twin(clusters,m):
  return [c for cl in clusters for c in half(far(cl,m),m)]

# ---- sum ----
def numstat(vals):
  s = sorted(vals); n = len(s)
  return o(mu = round(sum(s)/n,2),
           sd = round((s[int(.9*n)]-s[int(.1*n)])/2.56,2))

def symstat(vals):
  n = len(vals); c = {v:vals.count(v) for v in set(vals)}
  return o(n=n, ent=round(-sum(p/n*math.log2(p/n) for p in c.values()),2))

def _vals(rows,k): return [r[k] for r in rows if r[k]!="?"]

def summarize(cluster,m):
  return {m.hdr[k]:(numstat if m.col[k] else symstat)(_vals(cluster,k))
          for k in range(m.nc)}

# ---- acquire + learn ----
def acquire(clusters,best,m):
  return min(clusters,key=lambda c:dists(c[0],best,m))[0]

def learn(csv,rounds=4,labels=10,seed=42,oracle=None):
  m = prep(csv,seed)
  clusters = [m.rows]
  for _ in range(rounds):
    clusters = twin(clusters,m)
  clusters.sort(key=lambda c:yscore(c[0],m))
  log, best = [], clusters[0][0]
  for i in range(labels):
    log.append(o(label=i+1, row=best, score=(oracle or yscore)(best,m)))
    best = acquire(clusters,best,m)
  return o(clusters=clusters, log=log,
           summary=[summarize(c,m) for c in clusters])

# ---- tree ----
def _mean(a): return sum(a)/len(a) if a else 0

def _sd(a):
  if len(a)<2: return 0
  mu = _mean(a); return math.sqrt(sum((v-mu)**2 for v in a)/(len(a)-1))

def _mode(a): return max(set(a),key=a.count)

def _sval(k,top,bot,m):   # split value: midpoint (num) or mode of top (sym)
  a = _vals(top,k)
  if m.col[k]:
    b = _vals(bot,k)
    return (_mean(a)+_mean(b))/2 if a and b else None
  return _mode(a) if a else None

def _part(rows,k,v,m):    # partition; unknowns go right
  L,R = [],[]
  for r in rows:
    if r[k] != "?" and (r[k]<=v if m.col[k] else r[k]==v):
      L.append(r)
    else:
      R.append(r)
  return L,R

def grow(rows,m,stop=4,pre=""):
  node = o(rows=rows, pre=pre, kids=[])
  if len(rows) > stop*2:
    rs = sorted(rows, key=lambda r:yscore(r,m))
    n = len(rs)//2
    top,bot = rs[:n],rs[n:]
    bv,bk,bval = 1e32,None,None
    for k in m.xs:
      v = _sval(k,top,bot,m)
      if v is None: continue
      l,r = _part(rows,k,v,m)
      if not l or not r: continue
      yl = [yscore(x,m) for x in l]
      yr = [yscore(x,m) for x in r]
      w = _sd(yl)*len(l) + _sd(yr)*len(r)
      if w < bv: bv,bk,bval = w,k,v
    if bk is not None:
      l,r = _part(rows,bk,bval,m)
      h = m.hdr[bk]; f = f"{bval:.2f}" if m.col[bk] else str(bval)
      s1,s2 = ((f"{h}<={f}",f"{h}> {f}")
               if m.col[bk] else (f"{h}=={f}",f"{h}!={f}"))
      node.cut = (bk,bval)
      node.kids = [grow(l,m,stop,s1), grow(r,m,stop,s2)]
  return node

def leaf(node,row,m):
  if not node.kids: return node
  k,v = node.cut
  ok = row[k]!="?" and (row[k]<=v if m.col[k] else row[k]==v)
  return leaf(node.kids[0 if ok else 1],row,m)

def tshow(node,m,lvl=0,w=32):
  lbl = ('|  '*(lvl-1) if lvl else '')+node.pre
  if not node.kids:
    mu = _mean([yscore(r,m) for r in node.rows])
    print(f"{lbl:<{w}} n={len(node.rows):3d}  y={mu:.2f}")
  else:
    if lbl: print(lbl)
  for kid in node.kids: tshow(kid,m,lvl+1,w)

# far.awk
{ cluster() }

function cluster(   i,n,m,t) {
  n = load($0)
  m = n<20 ? n : 20
  poles(m)
  if(yscore(AI) > yscore(BI)) { t=AI; AI=BI; BI=t }
  swap(1,AI); swap(2,BI)
  for(i=1; i<=n; i++) emit(i)
  print "" }

function poles(m,   i,j,d,best) {
  best = -1
  for(i=1; i<=m; i++)
    for(j=i+1; j<=m; j++)
      if((d=dists(i,j)) > best) { best=d; AI=i; BI=j } }

function yscore(i,   k,v,d,n) {
  for(k=1; k<=nc; k++) if(k in ydir) {
    v = norm(R[i][k], lo[k], hi[k])
    d += (v - ydir[k])^2; n++ }
  return n ? sqrt(d/n) : 0 }

function swap(i,j,   k,t) {
  for(k=1; k<=nc; k++) { t=R[i][k]; R[i][k]=R[j][k]; R[j][k]=t } }

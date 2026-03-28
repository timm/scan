# lib.awk
BEGIN { RS=""; FS="\n" }

NR==1 { header(); print $0 ORS; next }

function header(   i) {
  nc = split($1, hdr, ",")
  split($2, L, ",")
  split($3, H, ",")
  for(i=1; i<=nc; i++) {
    if(isnum(L[i]))    { lo[i]=L[i]+0; hi[i]=H[i]+0 }
    if(hdr[i] ~  /-$/) ydir[i]=0
    if(hdr[i] ~ /\+$/) ydir[i]=1 } }

function load(s,   i,n,tmp,row,j) {
  n = split(s, tmp, "\n")
  for(i=1; i<=n; i++) {
    split(tmp[i], row, ",")
    for(j=1; j<=nc; j++)
      R[i][j] = (j in lo) ? row[j]+0 : row[j] }
  return n }

function dists(i,j,   k,d,n) {
  for(k=1; k<=nc; k++) {
    if(R[i][k]=="?" && R[j][k]=="?") return 1
    d += dist(R[i][k], R[j][k], k); n++ }
  return n ? sqrt(d/n) : 1 }

function dist(a,b,k,   v) {
  if(k in lo) {
    if(a=="?") { v=norm(b,lo[k],hi[k]); return v>0.5 ? v : 1-v }
    if(b=="?") { v=norm(a,lo[k],hi[k]); return v>0.5 ? v : 1-v }
    v = norm(a,lo[k],hi[k]) - norm(b,lo[k],hi[k])
    return v*v }
  return (a != b) }

function norm(v,lo,hi) { return (v-lo)/(hi-lo+1e-32) }
function isnum(v)      { return v+0 == v && v != "" }

function emit(i,   k) {
  for(k=1; k<=nc; k++) printf "%s%s", R[i][k], (k<nc ? "," : "\n") }

function repr(a,   keys,n,i,k,v,out) {
  n = asorti(a, keys)
  out = "["
  for(i=1; i<=n; i++) {
    k = keys[i]; v = a[k]
    out = out ":" k " "
    if   (isarray(v)) out = out repr(v)
    else if(isnum(v)) out = out (v==int(v) ? int(v) : sprintf("%.2f",v))
    else              out = out v
    if(i<n) out = out " " }
  return out "]" }

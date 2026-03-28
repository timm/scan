# half.awk
{ halve() }

function halve(   i,n,na,nb) {
  n = load($0)
  for(i=3; i<=n; i++)
    if(dists(i,1) <= dists(i,2)) A[++na]=i
    else                          B[++nb]=i
  emitCluster(1, A, na)
  emitCluster(2, B, nb)
  delete A; delete B }

function emitCluster(pole, side, ns,   i) {
  emit(pole)
  for(i=1; i<=ns; i++) emit(side[i])
  print "" }

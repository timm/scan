# sum.awk
{ summarize() }

function summarize(   i,k,n,row,rows) {
  n = split($0, rows, "\n")
  for(k=1; k<=nc; k++) { delete col[k]; col_n[k]=0 }
  for(i=1; i<=n; i++) {
    split(rows[i], row, ",")
    for(k=1; k<=nc; k++)
      if(row[k] != "?") col[k][++col_n[k]] = row[k] }
  for(k=1; k<=nc; k++) {
    printf "%s:", hdr[k]
    if(k in lo) numstat(col[k], col_n[k])
    else        symstat(col[k], col_n[k])
    printf (k<nc ? "  " : "\n")
    delete col[k] }
  print "" }

function numstat(a, n,   i,sum,mu) {
  for(i=1; i<=n; i++) sum += a[i]+0
  mu = sum/n
  asort(a)
  sd = (a[int(.9*n)+1] - a[int(.1*n)+1]) / 2.56
  printf "mu=%.2f sd=%.2f", mu, sd }

function symstat(a, n,   k,v,e,p,counts) {
  for(k=1; k<=n; k++) counts[a[k]]++
  for(v in counts) { p=counts[v]/n; e -= p*log(p)/log(2) }
  printf "ent=%.2f n=%d", e, n
  delete counts }

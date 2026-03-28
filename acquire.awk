# acquire.awk — nearest cluster mid to current best
BEGIN { RS=""; FS="\n"; split(best, B, ",") }

NR==1 { header(); next }
      { split($1, row, ",")
        for(k=1; k<=nc; k++) R[1][k] = (k in lo) ? row[k]+0 : row[k]
        for(k=1; k<=nc; k++) R[2][k] = (k in lo) ? B[k]+0   : B[k]
        d = dists(1,2)
        if(NR==2 || d < bestd) { bestd=d; pick=$1 } }

END   { print pick }

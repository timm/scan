# prep.awk
BEGIN { FS=OFS="," }

NR==1 { nc=split($0,hdr,","); next }
      { for(i=1;i<=nc;i++) {
          gsub(/[ \t]+/,"",$i)
          if($i=="" || $i~/^[Nn][Aa]$/) $i="?" }
        if(NR==2) initlo()
        update()
        a[rand()]=$0 }

END   { emitHeader(); for(k in a) print a[k]; print "" }

function initlo(   i) {
  for(i=1; i<=nc; i++)
    if($i != "?") { lo[i]=$i+0; hi[i]=$i+0 } }

function update(   i,v) {
  for(i=1; i<=nc; i++)
    if((i in lo) && $i!="?") {
      v=$i+0
      if(v<lo[i]) lo[i]=v
      if(v>hi[i]) hi[i]=v } }

function emitHeader(   i) {
  for(i=1;i<=nc;i++) printf "%s%s", hdr[i],  (i<nc ? OFS : ORS)
  for(i=1;i<=nc;i++) printf "%s%s", (i in lo ? lo[i] : "-"), (i<nc ? OFS : ORS)
  for(i=1;i<=nc;i++) printf "%s%s", (i in lo ? hi[i] : "-"), (i<nc ? OFS : ORS)
  print "" }

# run.sh
AWK='gawk -f lib.awk -f'
FAR="$AWK far.awk"
HALF="$AWK half.awk"
SUM="$AWK sum.awk"
ACQ="$AWK acquire.awk"

twin()  { $FAR | $HALF; }
prep()  { gawk -f lib.awk -f prep.awk "$1"; }
learn() {
  prep "$1" | twin | twin | twin | twin > /tmp/clusters.txt
  best=$(grep -m1 "" /tmp/clusters.txt)       # row1 of first cluster
  for i in 1 2 3 4 5 6 7 8 9 10; do
    echo "LABEL: $best"
    best=$(gawk -v best="$best" -f lib.awk -f acquire.awk /tmp/clusters.txt)
  done }

case "$1" in
  cluster) prep "$2" | twin | twin | twin | twin | $SUM ;;
  learn)   learn "$2" ;;
  *)       echo "usage: $0 cluster|learn file.csv" ;;
esac

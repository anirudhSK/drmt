#! /bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./benchmark.sh result_folder"
  exit
fi

for prog in switch_egress switch_ingress; do
    echo "drmt $prog"
    /usr/bin/time python drmt.py $prog yes > $1/drmt_${prog}.txt
    echo "prmt_fine $prog"
    /usr/bin/time python prmt.py $prog yes fine > $1/prmt_fine_${prog}.txt
    echo "prmt_coarse $prog"
    /usr/bin/time python prmt.py $prog yes coarse > $1/prmt_coarse_${prog}.txt
    echo -e "\n"
  done

#! /bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./benchmark.sh result_folder"
  exit
fi

for arch in drmt prmt_fine prmt_coarse; do
  for prog in switch_egress switch_ingress; do
    echo "$arch $prog"
    /usr/bin/time python $arch.py $prog yes > $1/${arch}_${prog}.txt
    echo -e "\n"
  done
done

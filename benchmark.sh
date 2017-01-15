#! /bin/bash

for arch in drmt prmt_fine prmt_coarse; do
  for prog in switch-orig-egress-ilp-input switch-orig-ingress-ilp-input; do
    for greedy in yes no; do
      echo "$arch $prog $greedy"
      time python $arch.py $prog $greedy > ${arch}_${prog}_${greedy}.txt
    done
  done
done

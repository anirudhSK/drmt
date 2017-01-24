#! /bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: ./run_experiments.sh result_folder"
  exit
fi

for prog in switch_combined switch_combined_subset switch_egress switch_egress_subset switch_ingress switch_ingress_subset;
do
  echo "drmt_ipc_1 $prog"
  /usr/bin/time python drmt.py large_hw      drmt_latencies 10 > $1/drmt_ipc_1_${prog}.txt
  echo "drmt_ipc_2 $prog"
  /usr/bin/time python drmt.py large_hw_ipc2 drmt_latencies 10 > $1/drmt_ipc_1_${prog}.txt
  echo "prmt_fine $prog"
  /usr/bin/time python prmt.py large_hw      prmt_latencies fine> $1/prmt_fine_${prog}.txt
  echo "prmt_coarse $prog"
  /usr/bin/time python prmt.py large_hw      prmt_latencies coarse> $1/prmt_coarse_${prog}.txt
  echo -e "\n"
done

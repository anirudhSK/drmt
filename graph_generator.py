import sys
import math
if (len(sys.argv) !=2):
  print("Usage: ", sys.argv[0], " <result folder>")
  exit(1)
else:
  result_folder = sys.argv[1]
LIMIT_PROC = 51

progs = ["switch_combined", "switch_combined_subset", "switch_egress",\
         "switch_egress_subset", "switch_ingress", "switch_ingress_subset"]
d_archs = ["drmt_ipc_1", "drmt_ipc_2"]
p_archs = ["prmt_coarse", "prmt_fine"]

pipeline_stages  = dict()
drmt_min_periods = dict()
drmt_thread_count= dict()

for prog in progs:
  for arch in d_archs + p_archs:
     fh = open(result_folder + "/" + arch + "_" + prog + ".txt", "r")
     for line in fh.readlines():
       if arch.startswith("prmt"):
         if "stages" in line:
           pipeline_stages[(prog, arch)] = float(line.split()[4])
       elif arch.startswith("drmt"):
         if "achieved throughput" in line:
           drmt_min_periods[(prog, arch)] = int(line.split()[7])
         if "thread count" in line:
           drmt_thread_count[(prog, arch)] = int(line.split()[5])
         if "Upper bound" in line:
           drmt_min_periods[(prog, "full_dagg")] = float(line.split()[5])
       else:
         print ("Unknown architecture")
         assert(False)

for prog in progs:
  for arch in p_archs:
    plot_file = open((prog + "_" + arch + ".dat"), "w")
    for n in range(1, LIMIT_PROC):
      print(n, max(1, 1/math.ceil(pipeline_stages[(prog, arch)]/n)), file = plot_file)

for prog in progs:
  for arch in d_archs:
    plot_file = open((prog + "_" + arch + ".dat"), "w")
    for n in range(1, LIMIT_PROC):
      print(n, max(1, n / drmt_min_periods[(prog, arch)]), file = plot_file)

for prog in progs:
  plot_file = open((prog + "_" + "full_dagg" + ".dat"), "w")
  for n in range(1, LIMIT_PROC):
    print(n, max(1, n / drmt_min_periods[(prog, "full_dagg")]), file = plot_file)

print("drmt thread count")
for prog in progs:
  for arch in d_archs:
    print(prog, arch, drmt_thread_count[(prog, arch)])

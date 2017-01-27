import sys
import math
import matplotlib
import importlib
matplotlib.use('Agg')
matplotlib.rcParams.update({'font.size':18})
import matplotlib.pyplot as plt
if (len(sys.argv) != 5):
  print("Usage: ", sys.argv[0], " <result folder> <drmt latencies> <prmt latencies> <folder for figs>")
  exit(1)
else:
  result_folder = sys.argv[1]
  drmt_latencies = importlib.import_module(sys.argv[2], "*")
  prmt_latencies = importlib.import_module(sys.argv[3], "*")
  fig_folder    = sys.argv[4]

PROCESSORS=range(1, 51)

progs = ["switch_egress"]
d_archs = ["drmt_ipc_1", "drmt_ipc_2"]
p_archs = ["prmt_coarse", "prmt_fine"]

labels = dict()
labels["drmt_ipc_1"] = "dRMT (IPC=1)"
labels["drmt_ipc_2"] = "dRMT (IPC=2)"
labels["prmt_coarse"]= "RMT"
labels["prmt_fine"]  = "RMT fine"
labels["upper_bound"] = "Upper bound"

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
         if "Searching between limits" in line:
           drmt_min_periods[(prog, "upper_bound")] = int(line.split()[3])
       else:
         print ("Unknown architecture")
         assert(False)

for prog in progs:
  plt.figure()
  plt.title("Throughput vs. Processors")
  plt.xlabel("Processors", fontsize = 26)
  plt.ylabel("Packets per cycle", fontsize = 26)
  
  plt.step(PROCESSORS, [min(1.0, 1.0 / math.ceil(pipeline_stages[(prog, "prmt_coarse")]/n)) for n in PROCESSORS], label = labels["prmt_coarse"], linewidth=4, linestyle = '-')
  plt.step(PROCESSORS, [min(1.0, 1.0 / math.ceil(pipeline_stages[(prog, "prmt_fine")]/n)) for n in PROCESSORS], label = labels["prmt_fine"], linewidth=4, linestyle = ':')

  plt.step(PROCESSORS, [min(1.0, (n * 1.0) / drmt_min_periods[(prog, "drmt_ipc_1")]) for n in PROCESSORS], label = labels["drmt_ipc_1"], linewidth=4, linestyle = '-.')

  plt.step(PROCESSORS, [min(1.0, (n * 1.0) / drmt_min_periods[(prog, "drmt_ipc_2")]) for n in PROCESSORS], label = labels["drmt_ipc_2"], linewidth=4, linestyle = '--')

  plt.legend(loc = "lower right")
  plt.xlim(0, 15)
  plt.tight_layout()
  plt.savefig(fig_folder + "/" + prog + ".pdf")

print("drmt thread count")
print("%26s %16s %16s %16s %16s %16s %16s %16s %16s"%(\
        "prog", "ipc_1_lat", "ipc_1_period", "ipc_1_thrs", "ipc_2_lat", "ipc_2_period", "ipc_2_thrs",  "drmt:max(dM, dA)", "prmt:dM+dA"))
for prog in progs:
  print("%26s %16d %16d %16d %16d %16d %16d %16d %16d" %(\
          prog,\
          int(drmt_thread_count[(prog, "drmt_ipc_1")]), \
          int(drmt_min_periods[(prog, "drmt_ipc_1")]),\
          int(math.ceil(drmt_thread_count[(prog, "drmt_ipc_1")] / drmt_min_periods[(prog, "drmt_ipc_1")])),\
          int(drmt_thread_count[(prog, "drmt_ipc_2")]), \
          int(drmt_min_periods[(prog, "drmt_ipc_2")]),\
          int(math.ceil(drmt_thread_count[(prog, "drmt_ipc_2")] / drmt_min_periods[(prog, "drmt_ipc_2")])),\
          max(drmt_latencies.dM, drmt_latencies.dA),
          prmt_latencies.dM + prmt_latencies.dA))

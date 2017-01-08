# Convenience variable to represent constant latency in cycles from a match operation
# to its next operation (either match or action)
dM = 3

# Similar to above, this represents action to next operation latency
dA = 1

# All nodes in the DAG. Each node is an operation
# annotated with its name, type, and either
# key width or number of fields for match or action respectively
nodes = {'M0' : {'type':'match', 'key_width':640}, \
         'M*' : {'type':'match', 'key_width':640}, \
         'M1' : {'type':'match', 'key_width':640}, \
         'A*' : {'type':'action', 'num_fields':8}, \
         'A1' : {'type':'action', 'num_fields':8}, \
         'A2' : {'type':'action', 'num_fields':8}}

# Dependencies between nodes 
edges = {('M0','M*') : {'delay':dM}, \
         ('M0','A*') : {'delay':dM}, \
         ('M*','A1') : {'delay':dM}, \
         ('A*','A1') : {'delay':dA}, \
         ('A1','M1') : {'delay':dA}, \
         ('M1','A2') : {'delay':dM}}

# Total number of processors in the system
num_procs = 3

# Maximum limit on action fields that can be updated
# in one cycle at one processor. These action fields
# can belong to different packets, but the total number
# of fields being updated must be under action_fields_limit.
action_fields_limit = 8

# Maximum limit on match units that can be in use in
# one cycle at one processor. Again, these units can be
# used by different packets, but the total number of units
# in use must be under match_unit_limit
match_unit_limit = 4

# Size of a match unit. All match keys are
# rounded up to the nearest multiple of match_unit_size
match_unit_size  = 160

# Maximum limit on the number of packets that can be performing
# actions on a single processor in any clock cycle. There is no
# point to making this larger than action_fields_limit, but in
# practice it can be much smaller.
action_proc_limit = 8

# Maximum limit on the number of packets that can be performing
# matches on a single processor in any clock cycle. Similar to
# action_proc_limit, but for matches.
match_proc_limit  = 4

# Throughput expected from the system. The ILP tries to schedule
# a packet every period_duration cycles to satisfy this throughput,
# where period_duration =
# int(math.ceil((1.0 * input_for_ilp.num_procs) / input_for_ilp.throughput))
throughput = 1.0

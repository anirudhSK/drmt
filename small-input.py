dM = 3
dA = 1

nodes = {'M0' : {'type':'match', 'key_width':640}, \
         'M*' : {'type':'match', 'key_width':640}, \
         'M1' : {'type':'match', 'key_width':640}, \
         'A*' : {'type':'action', 'num_fields':8}, \
         'A1' : {'type':'action', 'num_fields':8}, \
         'A2' : {'type':'action', 'num_fields':8}}
         
edges = {('M0','M*') : {'delay':dM}, \
         ('M0','A*') : {'delay':dM}, \
         ('M*','A1') : {'delay':dM}, \
         ('A*','A1') : {'delay':dA}, \
         ('A1','M1') : {'delay':dA}, \
         ('M1','A2') : {'delay':dM}}

num_procs = 3

key_width_limit = 640
action_fields_limit = 8
match_unit_limit = 4

action_proc_limit = 8
match_proc_limit = 4

throughput_numerator = 3
throughput_denominator = 3

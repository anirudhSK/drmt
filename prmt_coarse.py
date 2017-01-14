from gurobipy import *
import numpy as np
import collections
import importlib
import math
from sets import Set
from schedule_dag import ScheduleDAG
from greedy_prmt_solver import GreedyPrmtSolver
from timeline_printer import timeline_str
from fine_to_coarse import contract_dag
from resource_usage_printer import print_resource_usage
from solution import Solution
import networkx as nx

class PrmtCoarseSolver:
    def __init__(self, dag,
                 input_spec, init_schedule):
        self.G = dag
        self.input_spec          = input_spec
        self.init_schedule       = init_schedule

    def solve(self):
        """ Returns the optimal schedule

        Returns
        -------
        time_of_op : dict
            Timeslot for each operation in the DAG
        ops_at_time : defaultdic
            List of operations in each timeslot
        length : int
            Maximum latency of optimal schedule
        """
        nodes = self.G.nodes()
        match_nodes = self.G.nodes(select='match')
        action_nodes = self.G.nodes(select='action')
        edges = self.G.edges()
        (_, cplen) = self.G.critical_path()

        # Set T_MAX as the max of initial schedule + 1
        if (self.init_schedule is not None):
          T_MAX = max(self.init_schedule.values()) + 1
        else:
          T_MAX = 3 * cplen

        m = Model()

        # Create variables
        # t is the start time for each DAG node
        t = m.addVars(nodes, lb=0, ub=T_MAX, vtype=GRB.INTEGER, name="t")

        # indicator[v, t] = 1 if v is scheduled at t 
        indicator  = m.addVars(list(itertools.product(nodes, range(T_MAX))),\
                               vtype=GRB.BINARY, name="indicator")

        # The length of the schedule
        length = m.addVar(lb=0, ub=T_MAX, vtype=GRB.INTEGER, name="length")

        # Set objective: minimize length of schedule
        m.setObjective(length, GRB.MINIMIZE)

        # Set constraints

        # The length is the maximum of all t's
        m.addConstrs((t[v]  <= length for v in nodes), "constr_length_is_max")

        # Given v, indicator[v, t] is 1 for exactly one t
        m.addConstrs((sum(indicator[v, t] for t in range(T_MAX)) == 1 for v in nodes),\
                     "constr_unique_time")

        # t is T * indicator
        m.addConstrs(((t[v] == sum(time * indicator[v, time] for time in range(T_MAX)))\
                     for v in nodes),\
                     "constr_equality")

        # Respect dependencies in DAG
        m.addConstrs((t[v] - t[u] >= int(self.G.edge[u][v]['delay'] > 0) for (u,v) in edges),\
                     "constr_dag_dependencies")

        # Number of match units does not exceed match_unit_limit
        m.addConstrs((sum(math.ceil((1.0 * self.G.node[v]['key_width']) / self.input_spec.match_unit_size) * indicator[v, t]\
                      for v in match_nodes)\
                      <= self.input_spec.match_unit_limit for t in range(T_MAX)),\
                      "constr_match_units")

        # The action field resource constraint (similar comments to above)
        m.addConstrs((sum(self.G.node[v]['num_fields'] * indicator[v, t]\
                      for v in action_nodes)\
                      <= self.input_spec.action_fields_limit for t in range(T_MAX)),\
                      "constr_action_fields")

        # The num_procs constraint, length of schedule (i.e., length + 1)
        # is lesser than the number of stages
        m.addConstr(length + 1 <= self.input_spec.num_procs, "constr_num_procs")

        # Initialize schedule
        if (self.init_schedule is not None):
          for v in nodes:
            t[v].start = self.init_schedule[v]

        # Any time slot (r) can have match or action operations
        # from only match_proc_limit/action_proc_limit packets
        # TODO

        # Solve model
        m.optimize()

        # Construct schedule and usage in every time slot
        solution = Solution()
        solution.ops_at_time = collections.defaultdict(list)
        solution.length = int(length.x + 1)
        assert(solution.length == length.x + 1)
        for time_slot in range(solution.length):
          solution.match_units_usage[time_slot] = 0
          solution.action_fields_usage[time_slot] = 0
        for v in nodes:
            tv = int(t[v].x)
            solution.ops_at_time[tv].append(v)
            if self.G.node[v]['type'] == 'match':
               solution.match_units_usage[tv] += math.ceil((1.0 * self.G.node[v]['key_width'])/self.input_spec.match_unit_size)
            elif self.G.node[v]['type'] == 'action':
               solution.action_fields_usage[tv] += self.G.node[v]['num_fields']
            else:
               assert(False)
        return solution

try:
    # Cmd line args
    if (len(sys.argv) != 3):
      print "Usage: ", sys.argv[0], " <scheduling input file without .py suffix> <yes to seed with greedy, no to run ILP directly>"
      exit(1)
    elif (len(sys.argv) == 3):
      input_file = sys.argv[1]
      seed_greedy = bool(sys.argv[2] == "yes")

    # Input example
    input_spec = importlib.import_module(input_file, "*")
    G = contract_dag(input_spec)
    assert(nx.is_directed_acyclic_graph(G))

    print '{:*^80}'.format(' Input DAG ')
    G.print_report(input_spec)

    print '{:*^80}'.format(' Running Greedy Solver ')
    gsolver = GreedyPrmtSolver(G,
                               input_spec)
    gschedule = gsolver.solve()
    print '{:*^80}'.format(' Running ILP Solver ')
    # Directly feed in input_spec
    solver = PrmtCoarseSolver(G,
                              input_spec,
                              init_schedule = gschedule if seed_greedy else None)
    solution = solver.solve()

    print 'Number of pipeline stages: %f' % (math.ceil(solution.length))
    print '\n\n'

    print '{:*^80}'.format(' Schedule')
    print timeline_str(solution.ops_at_time, white_space=0, timeslots_per_row=4),'\n\n'
    print_resource_usage(input_spec, solution)

except GurobiError as e:
    print('Error code ' + str(e.errno) + ": " + str(e))

except AttributeError as e:
    print('Encountered an attribute error ' + str(e))

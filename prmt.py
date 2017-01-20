from gurobipy import *
import numpy as np
import collections
import importlib
import math
from schedule_dag import ScheduleDAG
from greedy_prmt_solver import GreedyPrmtSolver
from fine_to_coarse import contract_dag
from printers import *
from solution import Solution

class PrmtFineSolver:
    def __init__(self, dag,
                 input_spec, seed_greedy):
        self.G = dag
        self.input_spec          = input_spec
        self.seed_greedy         = seed_greedy

    def solve(self, solve_coarse):
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
        if self.seed_greedy:
          print ('{:*^80}'.format(' Running greedy heuristic '))
          gsolver = GreedyPrmtSolver(contract_dag(self.input_spec), self.input_spec)
          gschedule = gsolver.solve()
          # gschedule was obtained as a solution to the coarse-grained model.
          # it needs to be modified to support the fine-grained model
          # although any solution to prmt_coarse is a solution to prmt_fine
          fine_grained_schedule = dict()
          for v in gschedule:
            if v.endswith('TABLE'):
              fine_grained_schedule[v.strip('TABLE') + 'MATCH'] = gschedule[v] * 2;
              fine_grained_schedule[v.strip('TABLE') + 'ACTION'] = gschedule[v] * 2 + 1;
            else:
              assert(v.startswith('_condition') or v.endswith('ACTION')) # No match
              fine_grained_schedule[v] = gschedule[v] * 2 + 1;    

        print ('{:*^80}'.format(' Running ILP solver '))
        nodes = self.G.nodes()
        match_nodes = self.G.nodes(select='match')
        action_nodes = self.G.nodes(select='action')
        edges = self.G.edges()
        (_, cplen) = self.G.critical_path()

        # Set T_MAX as the max of initial schedule + 1
        if (self.seed_greedy):
          T_MAX = max(fine_grained_schedule.values()) + 1
        else:
          T_MAX = 3 * cplen

        m = Model()

        # Create variables
        # t is the start substage (one match and one action substage make an RMT stage) for each DAG node
        t = m.addVars(nodes, lb=0, ub=T_MAX, vtype=GRB.INTEGER, name="t")

        # k is the even/odd quotient for each DAG node, i.e., t = 2*k + 1 or 2*k
        k = m.addVars(nodes, lb=0, ub=T_MAX, vtype=GRB.INTEGER, name="k")

        # indicator[v, t] = 1 if v is at substage t 
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

        # Respect dependencies in DAG, threshold delays at 0
        m.addConstrs((t[v] - t[u] >= int(self.G.edge[u][v]['delay'] > 0) for (u,v) in edges),\
                     "constr_dag_dependencies")

        # matches can only happen at even time slots
        for v in match_nodes:
          m.addConstr(t[v] == 2 * k[v])

        # actions can only happen at odd time slots
        for v in action_nodes:
          m.addConstr(t[v] == 2 * k[v] + 1)

        # Further, if this is coarse-grained PRMT
        # then match and actions from the same table need
        # to happen at the same k
        if (solve_coarse):
          for match in match_nodes:
            for action in action_nodes:
              if (action.startswith("_condition")):
                continue
              assert(match.endswith('MATCH'))
              assert(action.endswith('ACTION'))
              m_table = match.strip('MATCH')
              a_table = action.strip('ACTION')
              if (m_table == a_table):
                m.addConstr(k[match] == k[action])

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

        # Initialize schedule
        if (self.seed_greedy):
          for v in nodes:
            t[v].start = fine_grained_schedule[v]

        # Any time slot (r) can have match or action operations
        # from only match_proc_limit/action_proc_limit packets
        # TODO

        # Solve model
        m.optimize()

        # Construct length of schedule
        # and usage in every time slot
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

if __name__ == "__main__":
  # Cmd line args
  if (len(sys.argv) != 4):
    print ("Usage: ", sys.argv[0], " <scheduling input file without .py suffix> <yes to seed with greedy> <coarse/fine>")
    exit(1)
  elif (len(sys.argv) == 4):
    input_file = sys.argv[1]
    assert((sys.argv[2] == "yes") or (sys.argv[2] == "no"))
    seed_greedy = bool(sys.argv[2] == "yes")
    assert((sys.argv[3] == "coarse") or (sys.argv[3] == "fine"))
    solve_coarse = bool(sys.argv[3] == "coarse")

  # Input example
  input_spec = importlib.import_module(input_file, "*")
  G = ScheduleDAG()
  G.create_dag(input_spec.nodes, input_spec.edges)
  
  print ('{:*^80}'.format(' Input DAG '))
  print_problem(G, input_spec)
  
  print ('{:*^80}'.format(' Scheduling PRMT fine '))
  solver = PrmtFineSolver(G, input_spec, seed_greedy)
  solution = solver.solve(solve_coarse)
  if (solution.length > 2 * input_spec.num_procs):
    print ("Exceeded num_procs, rejected!!!")
    exit(1)
  print ('Number of pipeline stages: %f' % (math.ceil(solution.length / 2.0)))
  print ('{:*^80}'.format(' Schedule'))
  print (timeline_str(solution.ops_at_time, white_space=0, timeslots_per_row=4), '\n\n')
  print_resource_usage(input_spec, solution)

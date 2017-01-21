from gurobipy import *
import numpy as np
import collections
import importlib
import math
from schedule_dag import ScheduleDAG
from printers import *
from solution import Solution
from prmt import PrmtFineSolver
from sieve_rotator import *

class DrmtScheduleSolver:
    def __init__(self, dag, input_spec, seed_prmt_fine, period_duration, minute_limit):
        self.G = dag
        self.input_spec = input_spec
        self.seed_prmt_fine = seed_prmt_fine
        self.period_duration = period_duration
        self.minute_limit    = minute_limit

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
        if (self.seed_prmt_fine):
          print ('{:*^80}'.format(' Running PRMT fine ILP solver '))
          psolver = PrmtFineSolver(self.G, self.input_spec, seed_greedy=True)
          solution = psolver.solve(solve_coarse = False)
          init_drmt_schedule = sieve_rotator(solution.ops_at_time, self.period_duration,\
                                             input_spec.dM, input_spec.dA)
          assert(init_drmt_schedule)
          Q_MAX = int(math.ceil((1.0 * (max(init_drmt_schedule.values()) + 1)) / self.period_duration))
        else:
          # Set Q_MAX based on critical path
          cpath, cplat = self.G.critical_path()
          Q_MAX = int(math.ceil(1.5 * cplat / self.period_duration))

        print ('{:*^80}'.format(' Running DRMT ILP solver '))
        T = self.period_duration
        nodes = self.G.nodes()
        match_nodes = self.G.nodes(select='match')
        action_nodes = self.G.nodes(select='action')
        edges = self.G.edges()

        m = Model()

        # Create variables
        # t is the start time for each DAG node in the first scheduling period
        t = m.addVars(nodes, lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER, name="t")

        # The quotients and remainders when dividing by T (see below)
        # qr[v, q, r] is 1 when t[v]
        # leaves a quotient of q and a remainder of r, when divided by T.
        qr  = m.addVars(list(itertools.product(nodes, range(Q_MAX), range(T))), vtype=GRB.BINARY, name="qr")

        # Is there any match/action from packet q in time slot r?
        # This is required to enforce limits on the number of packets that
        # can be performing matches or actions concurrently on any processor.
        any_match = m.addVars(list(itertools.product(range(Q_MAX), range(T))), vtype=GRB.BINARY, name = "any_match")
        any_action = m.addVars(list(itertools.product(range(Q_MAX), range(T))), vtype=GRB.BINARY, name = "any_action")

        # The length of the schedule
        length = m.addVar(lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER, name="length")

        # Set objective: minimize length of schedule
        m.setObjective(length, GRB.MINIMIZE)

        # Set constraints

        # The length is the maximum of all t's
        m.addConstrs((t[v]  <= length for v in nodes), "constr_length_is_max")

        # Given v, qr[v, q, r] is 1 for exactly one q, r, i.e., there's a unique quotient and remainder
        m.addConstrs((sum(qr[v, q, r] for q in range(Q_MAX) for r in range(T)) == 1 for v in nodes),\
                     "constr_unique_quotient_remainder")

        # This is just a way to write dividend = quotient * divisor + remainder
        m.addConstrs((t[v] == \
                      sum(q * qr[v, q, r] for q in range(Q_MAX) for r in range(T)) * T + \
                      sum(r * qr[v, q, r] for q in range(Q_MAX) for r in range(T)) \
                      for v in nodes), "constr_division")

        # Respect dependencies in DAG
        m.addConstrs((t[v] - t[u] >= self.G.edge[u][v]['delay'] for (u,v) in edges),\
                     "constr_dag_dependencies")

        # Number of match units does not exceed match_unit_limit
        # for every time step (j) < T, check the total match unit requirements
        # across all nodes (v) that can be "rotated" into this time slot.
        m.addConstrs((sum(math.ceil((1.0 * self.G.node[v]['key_width']) / self.input_spec.match_unit_size) * qr[v, q, r]\
                      for v in match_nodes for q in range(Q_MAX))\
                      <= self.input_spec.match_unit_limit for r in range(T)),\
                      "constr_match_units")

        # The action field resource constraint (similar comments to above)
        m.addConstrs((sum(self.G.node[v]['num_fields'] * qr[v, q, r]\
                      for v in action_nodes for q in range(Q_MAX))\
                      <= self.input_spec.action_fields_limit for r in range(T)),\
                      "constr_action_fields")

        # Any time slot (r) can have match or action operations
        # from only match_proc_limit/action_proc_limit packets
        # We do this in two steps.

        # First, detect if there is any (at least one) match/action operation from packet q in time slot r
        # if qr[v, q, r] = 1 for any match node, then any_match[q,r] must = 1 (same for actions)
        # Notice that any_match[q, r] may be 1 even if all qr[v, q, r] are zero
        m.addConstrs((sum(qr[v, q, r] for v in match_nodes) <= (len(match_nodes) * any_match[q, r]) \
                      for q in range(Q_MAX)\
                      for r in range(T)),\
                      "constr_any_match1");

        m.addConstrs((sum(qr[v, q, r] for v in action_nodes) <= (len(action_nodes) * any_action[q, r]) \
                      for q in range(Q_MAX)\
                      for r in range(T)),\
                      "constr_any_action1");

        # Second, check that, for any r, the summation over q of any_match[q, r] is under proc_limits
        m.addConstrs((sum(any_match[q, r] for q in range(Q_MAX)) <= self.input_spec.match_proc_limit\
                      for r in range(T)), "constr_match_proc")
        m.addConstrs((sum(any_action[q, r] for q in range(Q_MAX)) <= self.input_spec.action_proc_limit\
                      for r in range(T)), "constr_action_proc")

        # Seed initial values
        if self.seed_prmt_fine:
          for i in nodes:
            t[i].start = init_drmt_schedule[i]

        # Solve model
        m.setParam('TimeLimit', self.minute_limit * 60)
        m.optimize()
        ret = m.Status

        print ('Return code is ', ret)
        if (ret == GRB.INFEASIBLE):
          return None
        elif ((ret == GRB.TIME_LIMIT) or (ret == GRB.INTERRUPTED)):
          if (m.SolCount == 0):
            return None

        # Construct and return schedule
        self.time_of_op = {}
        self.ops_at_time = collections.defaultdict(list)
        self.length = int(length.x + 1)
        assert(self.length == length.x + 1)
        for v in nodes:
            tv = int(t[v].x)
            self.time_of_op[v] = tv
            self.ops_at_time[tv].append(v)

        # Compute periodic schedule to calculate resource usage
        self.compute_periodic_schedule()

        # Populate solution
        solution = Solution()
        solution.time_of_op = self.time_of_op
        solution.ops_at_time = self.ops_at_time
        solution.ops_on_ring = self.ops_on_ring
        solution.length = self.length
        solution.match_key_usage     = self.match_key_usage
        solution.action_fields_usage = self.action_fields_usage
        solution.match_units_usage   = self.match_units_usage
        solution.match_proc_usage    = self.match_proc_usage
        solution.action_proc_usage   = self.action_proc_usage
        return solution

    def compute_periodic_schedule(self):
        T = self.period_duration
        self.ops_on_ring = collections.defaultdict(list)
        self.match_key_usage = dict()
        self.action_fields_usage = dict()
        self.match_units_usage = dict()
        self.match_proc_set = dict()
        self.match_proc_usage = dict()
        self.action_proc_set = dict()
        self.action_proc_usage = dict()
        for t in range(T):
          self.match_key_usage[t]     = 0
          self.action_fields_usage[t] = 0
          self.match_units_usage[t]   = 0
          self.match_proc_set[t]      = set()
          self.match_proc_usage[t]    = 0
          self.action_proc_set[t]     = set()
          self.action_proc_usage[t]   = 0

        for v in self.G.nodes():
            k = self.time_of_op[v] / T
            r = self.time_of_op[v] % T
            self.ops_on_ring[r].append('p[%d].%s' % (k,v))
            if self.G.node[v]['type'] == 'match':
                self.match_key_usage[r] += self.G.node[v]['key_width']
                self.match_units_usage[r] += math.ceil((1.0 * self.G.node[v]['key_width'])/ self.input_spec.match_unit_size)
                self.match_proc_set[r].add(k)
                self.match_proc_usage[r] = len(self.match_proc_set[r])
            else:
                self.action_fields_usage[r] += self.G.node[v]['num_fields']
                self.action_proc_set[r].add(k)
                self.action_proc_usage[r] = len(self.action_proc_set[r])

if __name__ == "__main__":
  # Cmd line args
  if (len(sys.argv) != 5):
    print ("Usage: ", sys.argv[0], " <DAG file> <HW file> <# processors> <time limit in mins>")
    exit(1)
  elif (len(sys.argv) == 5):
    input_file = sys.argv[1]
    hw_file = sys.argv[2]
    num_procs = int(sys.argv[3])
    minute_limit = int(sys.argv[4])

  # Input specification
  input_spec = importlib.import_module(input_file, "*")
  hw_spec    = importlib.import_module(hw_file, "*")
  input_spec.action_fields_limit = hw_spec.action_fields_limit
  input_spec.match_unit_limit    = hw_spec.match_unit_limit
  input_spec.match_unit_size     = hw_spec.match_unit_size
  input_spec.action_proc_limit   = hw_spec.action_proc_limit
  input_spec.match_proc_limit    = hw_spec.match_proc_limit

  # Create G
  G = ScheduleDAG()
  G.create_dag(input_spec.nodes, input_spec.edges)
  cpath, cplat = G.critical_path()

  print ('{:*^80}'.format(' Input DAG '))
  tpt_upper_bound = print_problem(G, input_spec)
  tpt_lower_bound = 0.1 # Just for kicks
  print ('\n\n')

  # Try to max. throughput
  # We do this by min. the period
  period_lower_bound = int(math.ceil((1.0 * num_procs) / tpt_upper_bound))
  period_upper_bound = int(math.ceil((1.0 * num_procs) / tpt_lower_bound))
  period = period_upper_bound
  last_good_solution = None
  last_good_period   = None
  print ('Searching between limits ', period_lower_bound, ' and ', period_upper_bound, ' cycles')
  low = period_lower_bound
  high = period_upper_bound
  while (low <= high):
    assert(low > 0)
    assert(high > 0)
    period = int(math.ceil((low + high)/2.0))
    print ('period =', period, ' cycles')
    print ('{:*^80}'.format(' Scheduling DRMT '))
    solver = DrmtScheduleSolver(G, input_spec, seed_prmt_fine = False, period_duration = period, minute_limit = minute_limit)
    solution = solver.solve()
    if (solution):
      last_good_period   = period
      last_good_solution = solution
      high = period - 1
    else:
      low  = period + 1
  if (last_good_solution == None):
    print ("Best throughput so far is below ", tpt_lower_bound, " packets/cycle.")
    exit(1)

  print ('Best achieved throughput = %f packets / cycle' % (num_procs / last_good_period))
  print ('Schedule length (thread count) = %d cycles' % last_good_solution.length)
  print ('Critical path length = %d cycles' % cplat)

  print ('\n\n')

  print ('{:*^80}'.format(' First scheduling period on one processor'))
  print (timeline_str(last_good_solution.ops_at_time, white_space=0, timeslots_per_row=4),'\n\n')

  print ('{:*^80}'.format(' Steady state on one processor'))
  print ('{:*^80}'.format('p[u] is packet from u scheduling periods ago'))
  print (timeline_str(last_good_solution.ops_on_ring, white_space=0, timeslots_per_row=4), '\n\n')

  print_resource_usage(input_spec, last_good_solution)

from gurobipy import *
import numpy as np
import collections
import importlib
import math
from sets import Set
from schedule_dag import ScheduleDAG

class DrmtScheduleSolver:
    def __init__(self, dag, period_duration,
                 match_unit_size, match_unit_limit, action_fields_limit,
                 match_proc_limit, action_proc_limit):
        self.G = dag
        self.action_fields_limit = action_fields_limit
        self.period_duration     = period_duration
        self.match_unit_size     = match_unit_size
        self.match_unit_limit    = match_unit_limit
        self.match_proc_limit    = match_proc_limit
        self.action_proc_limit   = action_proc_limit

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
        m.addConstrs((sum(math.ceil((1.0 * self.G.node[v]['key_width']) / self.match_unit_size) * qr[v, q, r]\
                      for v in match_nodes for q in range(Q_MAX))\
                      <= self.match_unit_limit for r in range(T)),\
                      "constr_match_units")

        # The action field resource constraint (similar comments to above)
        m.addConstrs((sum(self.G.node[v]['num_fields'] * qr[v, q, r]\
                      for v in action_nodes for q in range(Q_MAX))\
                      <= self.action_fields_limit for r in range(T)),\
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
        m.addConstrs((sum(any_match[q, r] for q in range(Q_MAX)) <= self.match_proc_limit\
                      for r in range(T)), "constr_match_proc")
        m.addConstrs((sum(any_action[q, r] for q in range(Q_MAX)) <= self.action_proc_limit\
                      for r in range(T)), "constr_action_proc")

        # Solve model
        m.optimize()

        # Construct and return schedule
        self.time_of_op = {}
        self.ops_at_time = collections.defaultdict(list)
        self.length = 0
        maxt = 0
        mint = np.inf
        for v in nodes:
            tv = int(t[v].x)
            if tv > maxt:
                maxt = tv
            if tv < mint:
                mint = tv
            self.time_of_op[v] = tv
            self.ops_at_time[tv].append(v)
        lenq = maxt - mint + 1
        if lenq > self.length:
            self.length = lenq
        return (self.time_of_op, self.ops_at_time, self.length)

    def timeline_str(self, strs_at_time, white_space=2, timeslots_per_row=8):
        """ Returns a string representation of the schedule in the ops_at_time
            argument

        Parameters
        ----------
        strs_at_time : dict
            List of strings for each timeslot

        white_space : int
            Amount of white space per timeslot

        timeslots_per_row : int
            Number of timesteps in each row

        Returns
        -------
        timeline : string
            Printable string representation of schedule
        strlen : int
            Length of string for each timeslot
        """

        num_strs = sum(len(strs) for strs in strs_at_time.itervalues())
        strlen = max(max(len(s) for s in strs) for strs in strs_at_time.itervalues()) + white_space
        timeline_length = max(t for t in strs_at_time.iterkeys()) + 1
        strlen = max(strlen, len(str(timeline_length))+2)

        K = timeline_length / timeslots_per_row
        R = timeline_length % timeslots_per_row

        timeline = ''
        for k in range(K+1):
            if k < K:
                low = k * timeslots_per_row
                high = low + timeslots_per_row
            else:
                low = k * timeslots_per_row
                high = low + R

            maxstrs = 0
            for t in range(low, high):
                if t in strs_at_time:
                    maxstrs = max(maxstrs, len(strs_at_time[t]))

            if maxstrs > 0:
                timeline += '|'
                for t in range(low, high):
                    timeline += '{0: ^{1}}'.format('t=%d' % t, strlen) + '|'
                for i in range(maxstrs):
                    timeline += '\n|'
                    for t in range(low, high):
                        if (t in strs_at_time) and (i<len(strs_at_time[t])):
                            timeline += '{0: ^{1}}'.format(strs_at_time[t][i],strlen) + '|'
                        else:
                            timeline += ' ' * strlen + '|'
                timeline += '\n\n'

        return (timeline, strlen)

    def compute_periodic_schedule(self, unit_size):
        T = self.period_duration
        ops_on_ring = collections.defaultdict(list)
        match_key_usage = [0] * T
        action_fields_usage = [0] * T
        match_units_usage = [0] * T

        match_proc_set = [0] * T
        for t in range(T):
          match_proc_set[t] = Set()
        match_proc_usage = [0] * T

        action_proc_set = [0] * T
        for t in range(T):
          action_proc_set[t] = Set()
        action_proc_usage = [0] * T
        for v in self.G.nodes():
            k = self.time_of_op[v] / T
            r = self.time_of_op[v] % T
            ops_on_ring[r].append('p[%d].%s' % (k,v))
            if self.G.node[v]['type'] == 'match':
                match_key_usage[r] += self.G.node[v]['key_width']
                match_units_usage[r] += math.ceil((1.0 * self.G.node[v]['key_width'])/ unit_size)
                match_proc_set[r].add(k)
                match_proc_usage[r] = len(match_proc_set[r])
            else:
                action_fields_usage[r] += self.G.node[v]['num_fields']
                action_proc_set[r].add(k)
                action_proc_usage[r] = len(action_proc_set[r])
        # TODO: This is bad form. Return a struct instead.
        return (ops_on_ring, match_key_usage, action_fields_usage, match_units_usage, match_proc_usage, action_proc_usage)

try:
    # Cmd line args
    if (len(sys.argv) != 2):
      print "Usage: ", sys.argv[0], " <scheduling input file without .py suffix>"
      exit(1)
    elif (len(sys.argv) == 2):
      input_file = sys.argv[1]

    # Input example
    input_for_ilp = importlib.import_module(input_file, "*")

    # Derive period_duration from num_procs and throughput
    period_duration = int(math.ceil((1.0 * input_for_ilp.num_procs) / input_for_ilp.throughput))

    G = ScheduleDAG(input_for_ilp.nodes, input_for_ilp.edges)
    cpath, cplat = G.critical_path()

    Q_MAX = int(math.ceil(1.5 * cplat / period_duration))
    
    print '{:*^80}'.format(' Input DAG ')
    G.print_report(match_unit_size = input_for_ilp.match_unit_size,\
                   action_fields_limit = input_for_ilp.action_fields_limit, \
                   match_unit_limit = input_for_ilp.match_unit_limit, \
                   num_procs = input_for_ilp.num_procs, \
                   throughput = input_for_ilp.throughput, \
                   match_proc_limit = input_for_ilp.match_proc_limit, \
                   action_proc_limit = input_for_ilp.action_proc_limit)
    print 'Q_MAX = ', Q_MAX
    print '\n\n'

    print '{:*^80}'.format(' Running Solver ')
    solver = DrmtScheduleSolver(dag=G,
                                period_duration = period_duration, \
                                match_unit_size = input_for_ilp.match_unit_size, \
                                action_fields_limit= input_for_ilp.action_fields_limit, \
                                match_unit_limit = input_for_ilp.match_unit_limit,
                                action_proc_limit = input_for_ilp.action_proc_limit,
                                match_proc_limit = input_for_ilp.match_proc_limit)
    solver.solve()

    (timeline, strlen) = solver.timeline_str(solver.ops_at_time, white_space=0, timeslots_per_row=4)

    print 'Optimal schedule length = %d cycles' % solver.length
    print 'Critical path length = %d cycles' % cplat

    print '\n\n'

    print '{:*^80}'.format(' First scheduling period on one processor')
    print timeline,'\n\n'

    (ops_on_ring, match_key_usage, action_fields_usage, match_units_usage, match_proc_usage, action_proc_usage) = solver.compute_periodic_schedule(input_for_ilp.match_unit_size)
    (timeline, strlen) = solver.timeline_str(ops_on_ring, white_space=0, timeslots_per_row=4)
    print '{:*^80}'.format(' Steady state on one processor')
    print '{:*^80}'.format('p[u] is packet from u scheduling periods ago')
    print timeline, '\n\n'

    print 'Match units usage (max = %d units) on one processor' % input_for_ilp.match_unit_limit
    mu_usage = {}
    for t in range(period_duration):
        mu_usage[t] = [str(match_units_usage[t])]
    (timeline, strlen) = solver.timeline_str(mu_usage, white_space=0, timeslots_per_row=16)
    print timeline

    print 'Action fields usage (max = %d fields) on one processor' % input_for_ilp.action_fields_limit
    af_usage = {}
    for t in range(period_duration):
        af_usage[t] = [str(action_fields_usage[t])]
    (timeline, strlen) = solver.timeline_str(af_usage, white_space=0, timeslots_per_row=16)
    print timeline

    print 'Match packets (max = %d match packets) on one processor' % input_for_ilp.match_proc_limit
    mp_usage = {}
    for t in range(period_duration):
        mp_usage[t] = [str(match_proc_usage[t])]
    (timeline, strlen) = solver.timeline_str(mp_usage, white_space=0, timeslots_per_row=16)
    print timeline

    print 'Action packets (max = %d action packets) on one processor' % input_for_ilp.action_proc_limit
    ap_usage = {}
    for t in range(period_duration):
        ap_usage[t] = [str(action_proc_usage[t])]
    (timeline, strlen) = solver.timeline_str(ap_usage, white_space=0, timeslots_per_row=16)
    print timeline

except GurobiError as e:
    print('Error code ' + str(e.errno) + ": " + str(e))

except AttributeError as e:
    print('Encountered an attribute error ' + str(e))

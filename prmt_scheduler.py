from gurobipy import *
import numpy as np
import collections
import importlib
import math
from sets import Set
from schedule_dag import ScheduleDAG

class PrmtScheduleSolver:
    def __init__(self, dag,
                 match_unit_size, match_unit_limit, action_fields_limit):
        self.G = dag
        self.action_fields_limit = action_fields_limit
        self.match_unit_size     = match_unit_size
        self.match_unit_limit    = match_unit_limit

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
        m.addConstrs((t[v] - t[u] >= self.G.edge[u][v]['delay'] for (u,v) in edges),\
                     "constr_dag_dependencies")

        # Number of match units does not exceed match_unit_limit
        m.addConstrs((sum(math.ceil((1.0 * self.G.node[v]['key_width']) / self.match_unit_size) * indicator[v, t]\
                      for v in match_nodes)\
                      <= self.match_unit_limit for t in range(T_MAX)),\
                      "constr_match_units")

        # The action field resource constraint (similar comments to above)
        m.addConstrs((sum(self.G.node[v]['num_fields'] * indicator[v, t]\
                      for v in action_nodes)\
                      <= self.action_fields_limit for t in range(T_MAX)),\
                      "constr_action_fields")

        # Any time slot (r) can have match or action operations
        # from only match_proc_limit/action_proc_limit packets
        # We do this in two steps.
        # TODO

        # Solve model
        m.optimize()

        # Construct length of schedule
        # and usage in every time slot
        self.ops_at_time = collections.defaultdict(list)
        self.length = int(length.x + 1)
        assert(self.length == length.x + 1)
        self.match_units_usage = [0] * self.length
        self.action_fields_usage = [0] * self.length
        for v in nodes:
            tv = int(t[v].x)
            self.ops_at_time[tv].append(v)
            if self.G.node[v]['type'] == 'match':
               self.match_units_usage[tv] += math.ceil((1.0 * self.G.node[v]['key_width'])/self.match_unit_size)
            elif self.G.node[v]['type'] == 'action':
               self.action_fields_usage[tv] += self.G.node[v]['num_fields']
            else:
               assert(False)

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

try:
    # Cmd line args
    if (len(sys.argv) != 2):
      print "Usage: ", sys.argv[0], " <scheduling input file without .py suffix>"
      exit(1)
    elif (len(sys.argv) == 2):
      input_file = sys.argv[1]

    # Input example
    input_for_ilp = importlib.import_module(input_file, "*")
    G = ScheduleDAG(input_for_ilp.nodes, input_for_ilp.edges)
    cpath, cplat = G.critical_path()

    print '{:*^80}'.format(' Input DAG ')
    G.print_report(match_unit_size = input_for_ilp.match_unit_size,\
                   action_fields_limit = input_for_ilp.action_fields_limit, \
                   match_unit_limit = input_for_ilp.match_unit_limit, \
                   throughput = input_for_ilp.throughput, \
                   match_proc_limit = 1,\
                   action_proc_limit = 1,\
                   num_procs = 1)
    # match_proc_limit, action_proc_limit, and num_procs are not used

    print '{:*^80}'.format(' Running Solver ')
    solver = PrmtScheduleSolver(dag=G,
                                match_unit_size = input_for_ilp.match_unit_size, \
                                action_fields_limit= input_for_ilp.action_fields_limit, \
                                match_unit_limit = input_for_ilp.match_unit_limit)
    solver.solve()

    (timeline, strlen) = solver.timeline_str(solver.ops_at_time, white_space=0, timeslots_per_row=4)

    print 'Optimal schedule length = %d cycles' % solver.length
    print 'Critical path length = %d cycles' % cplat

    print '\n\n'

    print '{:*^80}'.format(' Schedule')
    print timeline,'\n\n'

    print 'Match units usage (max = %d units) on one processor' % input_for_ilp.match_unit_limit
    mu_usage = {}
    for t in range(solver.length):
      mu_usage[t] = [str(solver.match_units_usage[t])]
    (timeline, strlen) = solver.timeline_str(mu_usage, white_space=0, timeslots_per_row=16)
    print timeline

    print 'Action fields usage (max = %d fields) on one processor' % input_for_ilp.action_fields_limit
    af_usage = {}
    for t in range(solver.length):
      af_usage[t] = [str(solver.action_fields_usage[t])]
    (timeline, strlen) = solver.timeline_str(af_usage, white_space=0, timeslots_per_row=16)
    print timeline

except GurobiError as e:
    print('Error code ' + str(e.errno) + ": " + str(e))

except AttributeError as e:
    print('Encountered an attribute error ' + str(e))

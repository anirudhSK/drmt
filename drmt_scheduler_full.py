from gurobipy import *
import numpy as np
import networkx as nx
import collections
import importlib
import math
K_MAX=20
class ScheduleDAG(nx.DiGraph):
    def __init__(self, nodes, edges):
        nx.DiGraph.__init__(self)
        self.create_dag(nodes, edges)

    def create_dag(self, nodes, edges):
        """ Returns a DAG of match/action nodes

        Parameters
        ----------
        nodes : dict
                Annotated nodes
        edges : dict
                Annotated edges

        Returns
        -------
        G : NetworkX.DiGraph
            DAG

        Raises
        ------
        ValueError
            If graph is not a DAG

        """
        # add_nodes_from and add_edges_from
        # are inherited from nx.DiGraph
        self.add_nodes_from(nodes)
        self.add_edges_from(edges)

        if nx.is_directed_acyclic_graph(self) is False:
            raise ValueError('Input is not a DAG!')

        # Annotate nodes
        for u in self.nodes():
            self.node[u]['type'] = nodes[u]['type']
            if self.node[u]['type'] == 'match':
                self.node[u]['key_width'] = nodes[u]['key_width']
            elif self.node[u]['type'] == 'action':
                self.node[u]['num_fields'] = nodes[u]['num_fields']
            else:
                assert(False)

        # Annotate edges
        for (u,v) in self.edges():
            self.edge[u][v]['delay'] = edges[(u,v)]['delay']

    def critical_path(self):
        """Returns the critical (longest) path in the DAG, and its latency

        Parameters
        ----------
        G : NetworkX DiGraph
            DAG

        Returns
        -------
        path : list
            Longest path
        latency : int
            Latency of longest path

        """
        dist = {}  # stores [distance, node] pair
        for node in nx.topological_sort(self):
            # pairs of dist,node for all incoming edges
            pairs = [(dist[v][0] + self[v][u]['delay'], v) for v,u in self.in_edges(node)]
            if pairs:
                dist[node] = max(pairs)
            else:
                dist[node] = (0, node)
        node, (length, _) = max(dist.items(), key=lambda x: x[1])
        latency = length + 1 # one extra cycle for final operation
        path = []
        while length > 0:
            path.append(node)
            length, node = dist[node]
        return list(reversed(path)), latency

    def nodes(self, data=False, select='*'):
        """Returns list of nodes with optional data values and selection filter

        Parameters
        ----------
        data : bool
            Include annotation data per node
        select : string
            type of nodes ('*', 'match', or 'action')


        Returns
        -------
        nodelist : list
            List of nodes

        """
        nodelist = []
        for (u, d) in nx.DiGraph.nodes(self, data=True):
            if (select == '*') or (d['type'] == select):
                if data is False:
                    nodelist.append(u)
                else:
                    nodelist.append((u,d))
        return nodelist

    def print_report(self, key_width_limit, action_fields_limit, match_unit_limit, num_procs,
                     throughput_numerator, throughput_denominator):
        cpath, cplat = self.critical_path()
        print '# of nodes = ', self.number_of_nodes()
        print '# of edges = ', self.number_of_edges()
        print '# of matches = ', len(self.nodes(select='match'))
        print '# of actions = ', len(self.nodes(select='action'))

        match_bits = reduce(lambda acc, node: acc + self.node[node]['key_width'], self.nodes(select='match'), 0)
        print '# of match bits = ', match_bits
        print 'aggregate key_width_limit = ', num_procs * key_width_limit

        assert(key_width_limit % match_unit_limit == 0)
        unit_size = key_width_limit / match_unit_limit
        match_units = reduce(lambda acc, node: acc + math.ceil((1.0 * self.node[node]['key_width']) / unit_size), self.nodes(select='match'), 0)
        print '# of match units = ', match_units
        print 'aggregate match_unit_limit = ', num_procs * match_unit_limit

        action_fields = reduce(lambda acc, node: acc + self.node[node]['num_fields'], self.nodes(select='action'), 0)
        print '# of action fields = ', action_fields
        print 'aggregate action_fields_limit = ', num_procs * action_fields_limit

        print 'Critical path: ', cpath
        print 'Critical path length = %d cycles' % cplat

        print 'Required throughput: %d packets every %d cycles (%f)'%(\
              throughput_numerator,\
              throughput_denominator, \
              (1.0 * throughput_numerator) / throughput_denominator)

        throughput_upper_bound = \
              min((1.0 * action_fields_limit * num_procs) / action_fields,\
                  (1.0 * key_width_limit     * num_procs) / match_bits, \
                  (1.0 * match_unit_limit    * num_procs) / match_units)
        print 'Upper bound on throughput = ', throughput_upper_bound
        if ((throughput_numerator / throughput_denominator) > throughput_upper_bound) :
          print 'Throughput cannot be supported with the current resources'

class DrmtScheduleSolver:
    def __init__(self, dag, period_duration,
                 pkts_per_period,
                 key_width_limit, match_unit_limit, action_fields_limit,
                 match_proc_limit, action_proc_limit):
        self.G = dag
        self.pkts_per_period = pkts_per_period
        self.key_width_limit = key_width_limit
        self.action_fields_limit = action_fields_limit
        self.period_duration = period_duration
        self.match_unit_limit = match_unit_limit
        self.match_proc_limit  = match_proc_limit
        self.action_proc_limit = action_proc_limit

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
        Q = self.pkts_per_period
        T = self.period_duration
        nodes = self.G.nodes()
        match_nodes = self.G.nodes(select='match')
        action_nodes = self.G.nodes(select='action')
        edges = self.G.edges()

        m = Model()

        # Supress Gurobi output
        #m.setParam( 'OutputFlag', False )

        # Create variables
        # t is the start time for each node in each packet (there are a total of pkts_per_period packets),
        # relative to the first node in that packet.
        # This is why there are nodes * range(Q) variables
        t = m.addVars(list(itertools.product(nodes, range(Q))), lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER, name="t")

        # The start time of each packet, i.e., the root of each packet's DAG
        # These start times have to be under T because all packets must start
        # within T.  
        delta = m.addVars(range(Q), lb=0, ub=T-1, vtype=GRB.INTEGER, name="delta")

        # The remainders when dividing by T (see below)
        # s[v, q, j] is 1 when delta[q] + t[v, q]
        # leaves a remainder of j when divided by T.
        s = m.addVars(list(itertools.product(nodes, range(Q), range(T))), vtype=GRB.BINARY, name="s")

        # The quotients when dividing by T
        # encoded similarly to s above
        p = m.addVars(list(itertools.product(nodes, range(Q), range(K_MAX))), vtype=GRB.BINARY, name="p")

        # Temporary variable for boolean ANDs of s[v, q, j] * p[v, q, k] for each j and k
        s_and_p = m.addVars(list(itertools.product(nodes, range(Q), range(T), range(K_MAX))), vtype=GRB.BINARY, name="s_and_p")

        # The length of the schedule
        length = m.addVar(lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER, name="length")

        # Set objective: minimize length of schedule
        m.setObjective(length, GRB.MINIMIZE)

        # Set constraints

        # First packet starts at time 0
        m.addConstr(delta[0] == 0)
        #m.addConstrs(delta[q] <= delta[q+1] for q in range(Q-1)) #TODO: Why is this not required?

        # The length is the maximum of all t's
        m.addConstrs(t[v,q]  <= length for v in nodes for q in range(Q))

        # This is just a way to write dividend = divisor * quotient + remainder
        m.addConstrs(delta[q]+t[v,q] == sum(k * p[v,q,k] for k in range(K_MAX)) * T + sum(j*s[v,q,j] for j in range(T)) for v in nodes for q in range(Q))

        # For each packet (q), respect dependencies in DAG
        m.addConstrs(t[v,q] - t[u,q] >= self.G.edge[u][v]['delay'] for (u,v) in edges for q in range(Q))

        # Given v and q, s[v, q, j] is 1 for exactly one j < T, i.e., there's a unique remainder j
        m.addConstrs(sum(s[v,q,j] for j in range(T)) == 1 for v in nodes for q in range(Q))

        # Given v and q, p[v, q, k] is 1 for exactly one k < K_MAX, i.e., there's a unique quotient k
        m.addConstrs(sum(p[v,q,k] for k in range(K_MAX)) == 1 for v in nodes for q in range(Q))

        # The key width resource constraint:
        # for every time step (j) < T, check the total key width requirement
        # across all packets (q) and their nodes (v) that
        # can be "rotated" into this time slot.
        m.addConstrs(sum(self.G.node[v]['key_width']*s[v,q,j] for v in match_nodes for q in range(Q)) <= self.key_width_limit for j in range(T))

        # Number of match units does not exceed match_unit_limit (similar comments to above)
        assert(self.key_width_limit % self.match_unit_limit == 0)
        unit_size = self.key_width_limit / self.match_unit_limit
        m.addConstrs(sum(math.ceil((1.0 * self.G.node[v]['key_width']) / unit_size ) * s[v,q,j] for v in match_nodes for q in range(Q)) <= self.match_unit_limit for j in range(T))

        # The action field resource constraint (similar comments to above)
        m.addConstrs(sum(self.G.node[v]['num_fields']*s[v,q,j] for v in action_nodes for q in range(Q)) <= self.action_fields_limit for j in range(T))

        # Any time slot (j) can have match or action operations from only one packet
        # Mathematically, for each j, Summation (v, q, k) s[v, q, j] * p[v, q, k]  <= 1
        # The summation is across
        # 1. either match or action vs,
        # 2. all q's
        # 3. all previous time periods (k)
        # This works because the summation picks out those terms for which s[v, q, j] == 1
        # i.e., all v's and q's that fall in that time slot
        # equivalently Summation(all v, q falling into j)(all k) p[v, q, k] <= 1
        # i.e., there's at most one k for which p[v, q, k] for all v, q falling into j
        m.addConstrs((2 * s_and_p[v, q, j, k]) >= (s[v, q, j] + p[v, q, k] - 1) for v in nodes for q in range(Q) for j in range(T) for k in range(K_MAX))
        m.addConstrs((2 * s_and_p[v, q, j, k]) <= (s[v, q, j] + p[v, q, k]) for v in nodes for q in range(Q) for j in range(T) for k in range(K_MAX))

        # At most one packet is doing a match or action every cycle
        m.addConstrs(sum(s_and_p[v, q, j, k] for v in match_nodes for q in range(Q) for k in range(K_MAX)) <= self.match_proc_limit for j in range(T))
        m.addConstrs(sum(s_and_p[v, q, j, k] for v in action_nodes for q in range(Q) for k in range(K_MAX)) <= self.action_proc_limit for j in range(T))

        # Read previous solution
        if (initial_solution != ""):
          m.read(initial_solution)

        # Solve model
        m.optimize()

        # Write solution
        assert(solution_output != "")
        m.write(solution_output)

        # Construct and return schedule
        self.time_of_op = {}
        self.ops_at_time = collections.defaultdict(list)
        self.length = 0
        for q in range(Q):
            maxt = 0
            mint = np.inf
            for v in nodes:
                # Add starting time of packet (delta[q]) with
                # time offset to this node (t[v,q])
                tvq = int(delta[q].x + t[v,q].x)
                if tvq > maxt:
                    maxt = tvq
                if tvq < mint:
                    mint = tvq
                self.time_of_op[v,q] = tvq
                self.ops_at_time[tvq].append('p['+str(q)+'].'+v)
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

    def compute_periodic_schedule(self):
        T = self.period_duration
        ops_on_ring = collections.defaultdict(list)
        match_key_usage = [0] * T
        action_fields_usage = [0] * T

        for q in range(self.pkts_per_period):
            for v in self.G.nodes():
                k = self.time_of_op[v,q] / T
                r = self.time_of_op[v,q] % T
                ops_on_ring[r].append('p[%d,%d].%s' % (k,q,v))
                if self.G.node[v]['type'] == 'match':
                    match_key_usage[r] += self.G.node[v]['key_width']
                else:
                    action_fields_usage[r] += self.G.node[v]['num_fields']

        return (ops_on_ring, match_key_usage, action_fields_usage)

try:
    # Cmd line args
    if (len(sys.argv) < 3):
      print "Usage: ", sys.argv[0], " <scheduling input file without .py suffix> <solution output> [initial solution]"
      exit(1)
    elif (len(sys.argv) == 3):
      input_file = sys.argv[1]
      solution_output = sys.argv[2]
      assert(solution_output.endswith(".mst"))
      initial_solution = ""
    elif (len(sys.argv) == 4):
      input_file = sys.argv[1]
      solution_output = sys.argv[2]
      assert(solution_output.endswith(".mst"))
      initial_solution = sys.argv[3]
      assert(initial_solution.endswith(".mst"))
    else:
      assert(False)

    # Input example
    input_for_ilp = importlib.import_module(input_file, "*")

    # Derive pkts_per_period from num_procs and throughput_numerator
    assert(input_for_ilp.throughput_numerator % input_for_ilp.num_procs == 0)
    pkts_per_period = input_for_ilp.throughput_numerator / input_for_ilp.num_procs
    period_duration = input_for_ilp.throughput_denominator

    G = ScheduleDAG(input_for_ilp.nodes, input_for_ilp.edges)
    period = period_duration

    print '{:*^80}'.format(' Input DAG ')
    G.print_report(key_width_limit = input_for_ilp.key_width_limit,\
                   action_fields_limit = input_for_ilp.action_fields_limit, \
                   match_unit_limit = input_for_ilp.match_unit_limit, \
                   num_procs = input_for_ilp.num_procs, \
                   throughput_denominator = input_for_ilp.throughput_denominator, \
                   throughput_numerator = input_for_ilp.throughput_numerator)

    print '\n\n'

    print '{:*^80}'.format(' Running Solver ')
    solver = DrmtScheduleSolver(dag=G,
                                pkts_per_period = pkts_per_period,\
                                period_duration = period_duration, \
                                key_width_limit = input_for_ilp.key_width_limit, \
                                action_fields_limit= input_for_ilp.action_fields_limit, \
                                match_unit_limit = input_for_ilp.match_unit_limit,
                                action_proc_limit = input_for_ilp.action_proc_limit,
                                match_proc_limit = input_for_ilp.match_proc_limit)
    solver.solve()

    (timeline, strlen) = solver.timeline_str(solver.ops_at_time, white_space=0, timeslots_per_row=4)

    print 'Optimal schedule length = %d cycles' % solver.length
    cpath, cplat = G.critical_path()
    print 'Critical path length = %d cycles' % cplat

    print '\n\n'

    print '{:*^80}'.format(' First scheduling period on one processor')
    print '{:*^80}'.format('p[i] is packet i from the first scheduling period')
    print timeline,'\n\n'

    (ops_on_ring, match_key_usage, action_fields_usage) = solver.compute_periodic_schedule()
    (timeline, strlen) = solver.timeline_str(ops_on_ring, white_space=0, timeslots_per_row=4)
    print '{:*^80}'.format(' Steady state on one processor')
    print '{:*^80}'.format('p[u, v] is packet v from u scheduling periods ago')
    print timeline, '\n\n'

    print '{:*^80}'.format(' Resource usage ')
    print 'Match key length usage (max = %d bits) on one processor' % input_for_ilp.key_width_limit
    mk_usage = {}
    for t in range(period):
        mk_usage[t] = [str(match_key_usage[t])]
    (timeline, strlen) = solver.timeline_str(mk_usage, white_space=0, timeslots_per_row=16)
    print timeline

    print 'Action fields usage (max = %d fields) on one processor' % input_for_ilp.action_fields_limit
    af_usage = {}
    for t in range(period):
        af_usage[t] = [str(action_fields_usage[t])]
    (timeline, strlen) = solver.timeline_str(af_usage, white_space=0, timeslots_per_row=16)
    print timeline


except GurobiError as e:
    print('Error code ' + str(e.errno) + ": " + str(e))

except AttributeError as e:
    print('Encountered an attribute error ' + str(e))

import networkx as nx
import math

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
                # TODO: Fix this and handle conditions correctly
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
        dist = {}  # stores [distance, node] pair.
        # distance is distance from root and node is predecessor on path from root
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

    def print_report(self, match_unit_size, action_fields_limit,
                     match_unit_limit, num_procs, throughput,
                     match_proc_limit, action_proc_limit):
        cpath, cplat = self.critical_path()
        print '# of processors = ', num_procs
        print '# of nodes = ', self.number_of_nodes()
        print '# of edges = ', self.number_of_edges()
        print '# of matches = ', len(self.nodes(select='match'))
        print '# of actions = ', len(self.nodes(select='action'))
        print 'Match unit size = ', match_unit_size

        match_units = reduce(lambda acc, node: acc + math.ceil((1.0 * self.node[node]['key_width']) / match_unit_size), self.nodes(select='match'), 0)
        print '# of match units = ', match_units
        print 'aggregate match_unit_limit = ', num_procs * match_unit_limit

        action_fields = reduce(lambda acc, node: acc + self.node[node]['num_fields'], self.nodes(select='action'), 0)
        print '# of action fields = ', action_fields
        print 'aggregate action_fields_limit = ', num_procs * action_fields_limit

        print 'match_proc_limit =', match_proc_limit
        print 'action_proc_limit =', action_proc_limit

        print 'Critical path: ', cpath
        print 'Critical path length = %d cycles' % cplat

        print 'Required throughput: %d packets / cycle '%(throughput)
        throughput_upper_bound = \
              min((1.0 * action_fields_limit * num_procs) / action_fields,\
                  (1.0 * match_unit_limit    * num_procs) / match_units)
        print 'Upper bound on throughput = ', throughput_upper_bound
        if (throughput > throughput_upper_bound) :
          print 'Throughput cannot be supported with the current resources'



import networkx as nx
import math

# For now, assume conditions cost 1 action field
CONDITION_COST = 1

# A DAG to represent fine-grained match-action scheduling constraints in dRMT and pRMT
class ScheduleDAG(nx.DiGraph):
    def __init__(self):
        nx.DiGraph.__init__(self)

    def create_dag(self, nodes, edges, latency_spec):
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
            elif self.node[u]['type'] == 'condition':
                # TODO: At some later point, we might handle conditions more carefully
                # For now, we treat them as actions with 1 action field
                self.node[u]['num_fields'] = CONDITION_COST
                self.node[u]['type'] = 'action'
            else:
                print ("Found unexpected node type ", self.node[u]['type'])
                assert(False)

        # Annotate edges
        for (u,v) in self.edges():
            # assign delay based on dependency type
            # see https://github.com/jafingerhut/p4-hlir#sched_data-dependency-graphs
            dep_type = edges[(u,v)]['dep_type']
            if (dep_type == 'new_match_to_action') or (dep_type == 'new_successor_conditional_on_table_result_action_type'):
              # minimum match latency
              self.edge[u][v]['delay'] = latency_spec.dM
            elif (dep_type == 'rmt_reverse_read') or (dep_type == 'rmt_successor'):
              # latency of dS, for now zero
              self.edge[u][v]['delay'] = latency_spec.dS
            elif (dep_type == 'rmt_action') or (dep_type == 'rmt_match'):
              # minimum action latency
              self.edge[u][v]['delay'] = latency_spec.dA
            else:
              print ("Unexpected dependency type: ", dep_type)
              assert(False)

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

import networkx as nx
import math
import collections

class GreedyPrmtSolver:
    def __init__(self, dag,
                 input_spec):
        self.G = dag
        self.input_spec = input_spec

    def solve(self):
        dist = {}  # stores distance of every node from root
        for node in nx.topological_sort(self.G): # TODO: Aren't all delays here either 0 or 1?
            distances = [(dist[v] + int(self.G[v][u]['delay'] > 0)) for v,u in self.G.in_edges(node)]
            if distances:
                dist[node] = max(distances)
            else:
                dist[node] = 0
        self.length = max(dist.values()) + 1 # one extra cycle for final operation

        # now get nodes at each distance
        nodes_at_dist = [0] * self.length
        for i in range(self.length):
          nodes_at_dist[i] = []
        for node in dist:
          nodes_at_dist[dist[node]] += [node]

        # Find start stage of each node/table
        current_stage = 0
        nodes_at_current_stage = []
        schedule = {}
        for i in range(self.length):
          # topo. sort subgraph induced by nodes_at_dist to ensure it meets 0-length dependencies
          work_list = nx.topological_sort(self.G.subgraph(nodes_at_dist[i]))
          for node in work_list:
            if (self.check_usage(nodes_at_current_stage + [node])):
              schedule[node] = current_stage
              nodes_at_current_stage += [node]
            else: # need a new stage for resource reasons
              assert(self.check_usage([node])) # otherwise problem is infeasible
              current_stage += 1
              schedule[node] = current_stage
              nodes_at_current_stage = [node]
          current_stage += 1 # This is a dependency relationship
          nodes_at_current_stage = [] # Reset nodes

        # Now inflate self.length to real value
        self.length = current_stage # we already added one in the last iteration of the previous loop

        # Compute ops on every time slot
        self.ops_at_time = collections.defaultdict(list)
        self.match_units_usage = dict()
        for time_slot in range(self.length): self.match_units_usage[time_slot] = 0
        self.action_fields_usage = dict()
        for time_slot in range(self.length): self.action_fields_usage[time_slot] = 0
        for v in self.G.nodes():
          tv = schedule[v]
          self.ops_at_time[tv].append(v)
          assert(self.G.node[v]['type'] == 'table')
          self.match_units_usage[tv] += math.ceil((1.0 * self.G.node[v]['key_width'])/self.input_spec.match_unit_size)
          self.action_fields_usage[tv] += self.G.node[v]['num_fields']
        return schedule
 
    def check_usage(self, work_list):
      match_units_usage = 0
      action_fields_usage = 0
      for v in work_list:
        assert(self.G.node[v]['type'] == 'table')
        match_units_usage += math.ceil((1.0 * self.G.node[v]['key_width'])/self.input_spec.match_unit_size)
        action_fields_usage += self.G.node[v]['num_fields']
      return (match_units_usage <= self.input_spec.match_unit_limit) and \
             (action_fields_usage <= self.input_spec.action_fields_limit)

import sys
import importlib
import networkx as nx
from schedule_dag import ScheduleDAG

def contract_dag(input_spec):
  G = ScheduleDAG()
  G.create_dag(input_spec.nodes, input_spec.edges)
  
  action_nodes = G.nodes(select='action')
  match_nodes  = G.nodes(select='match')
  
  tables = []
  found_table = dict()
  
  for m in match_nodes:
    for a in action_nodes:
      if (a.startswith("_condition")):
        continue
      assert(m.endswith('MATCH'))
      assert(a.endswith('ACTION'))
      m_table = m.strip('MATCH')
      a_table = a.strip('ACTION')
      if (m_table == a_table):
        tables.append((m, a))
        found_table[m] = True
        found_table[a] = True
  
  for m in match_nodes:
    if m not in found_table:
      print "Unpaired match, ERROR!!!"
      exit(1)
  
  for a in action_nodes:
    if (a.startswith("_condition")):
      continue
    if a not in found_table:
      print "Unpaird action: ", a
  
  # Contract table edges
  for table in tables:
    G = nx.contracted_edge(G, table, self_loops=False)

  return G

import sys
import importlib
import networkx as nx
from   schedule_dag import ScheduleDAG

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
      print ("Unpaired match, ERROR!!!")
      exit(1)
  
  for a in action_nodes:
    if a not in found_table:
      pass
  #    print ("Unpaired action or condition: ", a, file=sys.stderr)
 
  # Contract table edges
  for table in tables:
    match  = table[0]
    action = table[1]
    table_name = match.strip('MATCH') + 'TABLE'
    key_width  = G.node[match]['key_width']
    num_fields = G.node[action]['num_fields']
    G = nx.contracted_edge(G, table, self_loops=False)
    nx.relabel_nodes(G, {match: table_name}, False)
    G.node[table_name]['type'] = 'table'
    G.node[table_name]['key_width'] = key_width
    G.node[table_name]['num_fields'] = num_fields

  # Create dummy tables for the rest
  for v in G.nodes():
    if (G.node[v]['type'] != 'table'):
      G.node[v]['type'] = 'table'
      G.node[v]['key_width'] = 0
      assert(G.node[v]['num_fields'] >= 0)
      # leave num_fields unchanged

  return G

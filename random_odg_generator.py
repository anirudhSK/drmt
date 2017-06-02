# -*- coding: utf-8 -*-
"""
Created on Fri Jun 02 15:55:25 2017

@author: svar1984
"""
import networkx as nx
import numpy as np

# range for expected node degrees
low = 1
high = 5

# number of nodes
n = 10

# delays
dm = 22
da = 2
ds = 0

# sequence of expected degrees
w = np.random.randint(low,high,n)

# create the graph
G = nx.expected_degree_graph(w, seed=None, selfloops=False)

# remove degree 0 nodes
for node in G.nodes():

  if G.degree(node) == 0:
    G.remove_node(node)
    
# pick a source node and make the graph directed
s = np.random.choice(G.nodes())

DAG = nx.bfs_tree(G, s, reverse=False)

t_nodes = DAG.nodes()
t_edges = DAG.edges()

nodes = {}
edges = {}

# node att.
for node in t_nodes:
        
  node_type = np.random.choice(['_condition_','_MATCH','_ACTION'], p=[0.1, 0.45, 0.45])
      
  if node_type == '_MATCH':
      
    key_width = int(min(640, 80*np.random.geometric(.8, 1)))
            
    nodes[str(node)+node_type] = {'key_width': key_width, 'type': 'match', 'ID': node}
    
           
  elif node_type == '_ACTION':
    
    num_fields = int(min(32, np.random.geometric(.2, 1)))
        
    nodes[str(node)+node_type] = {'num_fields': num_fields, 'type': 'action', 'ID': node}
    
  else:
        
    nodes[node_type + str(node)] = {'num_fields': 0, 'type': 'condition', 'ID': node}

# edge att.
for edge in t_edges: 

  u, v = edge
    
  source = None
  destination = None
  
  for node in nodes:
    
    if nodes[node]['ID'] == u:
      
      source = node
      delay_type = nodes[node]['type']
      
    elif nodes[node]['ID'] == v:
      
      destination = node
  
  
  if delay_type == 'condition':
    
    delay = ds
    
  elif delay_type == 'action':
       
    delay = da
   
  else:
    
    delay = dm

  edges[(source, destination)] = {'delay': delay, 'dep_type': 'TODO'}
print nodes
print edges

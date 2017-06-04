
import networkx as nx
import numpy as np


def digraph_generator(n):
    
    G = nx.DiGraph()
     
    # We want c*n edges. 
    c = 5
    
    # We have (n^2-n)/2 possible edges. We want c*n edges. p = c*n / (n^2-n)/2.
    p = np.ceil(1/(float(2*c*n)/(n*n-n)))
    
    # create DAG.
    for i in range(0,n):
        for j in range(i+1,n):
            if not (np.random.random_integers(0, p)):
                G.add_edge(i,j)
                
    # nx.draw(G)
    
    return G
    
def odg_attr_generator(G, delays):
    
    nodes = {}
    edges = {}
    
    dm = delays['m']
    da = delays['a']
    ds = delays['c']   

    # Create nodes.    
    for node in nx.topological_sort(G):
      
      # conditional nodes are not leaves.
      successors = G.successors(node)
        
      if successors:
        
          node_type = np.random.choice(['_condition_','MATCH_ACTION','P_ACTION'], p=[0.25, 0.6, 0.15])
          
      else:
          
          node_type = np.random.choice(['MATCH_ACTION','P_ACTION'], p=[0.85, 0.15])
          
      # match then action nodes.    
      if node_type == 'MATCH_ACTION':
          
          
        # Geometric
        key_width = 80*int(min(np.random.geometric(.75, 1),8))
        
        # uniform
        # key_width = 80*np.random.random_integers(1, 8)
                
        nodes[str(node)+'_MATCH'] = {'key_width': key_width, 'type': 'match', 'ID': node}
        
        # Geometric
        num_fields = int(min(np.random.geometric(.25, 1),32))
        
        # uniform
        # num_fields = np.random.random_integers(1, 32)
        
        nodes[str(node)+'_ACTION'] = {'num_fields': num_fields, 'type': 'action', 'ID': node}
        
        # Create corresponding edge
        edges[(str(node)+'_MATCH', str(node)+'_ACTION')] = {'delay': dm, 'dep_type': 'new_match_to_action'}
        
      # Action with no corresponding match.                         
      elif node_type == 'P_ACTION':
          
        # Geometric
        num_fields = int(min(np.random.geometric(.25, 1),32))
        
        # uniform
        # num_fields = np.random.random_integers(1, 32)
            
        nodes[str(node)+node_type] = {'num_fields': num_fields, 'type': 'action', 'ID': node}
      
      # Condition.          
      else:
            
        nodes[node_type + str(node)] = {'num_fields': 1, 'type': 'condition', 'ID': node}

        
    # Create edges.        
    for node in nx.topological_sort(G):
        
      # name according to ID
      n_node = [name for name in nodes if nodes[name]['ID']==node][0]
      
      successors = G.successors(node)
        
      for dest in successors:
          
          # name according to ID                        
          n_dest = [name for name in nodes if nodes[name]['ID']==dest][0] 

          # match-action edges allready exist.  
          if  (n_node, n_dest) not in edges:            

              # TODO: fill correct 'dep_type'.                         
                                        
              if nodes[n_node]['type'] == 'match' and nodes[n_dest]['type'] == 'match':
                                
                edges[(n_node, n_dest)] = {'delay': dm, 'dep_type': 'new_match_to_action'}
    
              if nodes[n_node]['type'] == 'match' and nodes[n_dest]['type'] == 'action':
                                
                edges[(n_node, n_dest)] = {'delay': dm, 'dep_type': 'new_match_to_action'}
                
              if nodes[n_node]['type'] == 'match' and nodes[n_dest]['type'] == 'condition':
                                
                edges[(n_node, n_dest)] = {'delay': dm, 'dep_type': 'new_match_to_action'}
    
                
                
              if nodes[n_node]['type'] == 'action' and nodes[n_dest]['type'] == 'match':
                                
                edges[(n_node, n_dest)] = {'delay': da, 'dep_type': 'rmt_match'}
    
              if nodes[n_node]['type'] == 'action' and nodes[n_dest]['type'] == 'action':
                                
                edges[(n_node, n_dest)] = {'delay': da, 'dep_type': 'rmt_match'}
    
              if nodes[n_node]['type'] == 'action' and nodes[n_dest]['type'] == 'condition':
                                
                edges[(n_node, n_dest)] = {'delay': da, 'dep_type': 'rmt_match'}
                
                
    
              if nodes[n_node]['type'] == 'condition' and nodes[n_dest]['type'] == 'match':
                                
                edges[(n_node, n_dest)] = {'delay': ds, 'dep_type': 'rmt_successor'}
    
              if nodes[n_node]['type'] == 'condition' and nodes[n_dest]['type'] == 'action':
                                
                edges[(n_node, n_dest)] = {'delay': ds, 'dep_type': 'rmt_successor'}
    
              if nodes[n_node]['type'] == 'condition' and nodes[n_dest]['type'] == 'condition':
                                
                edges[(n_node, n_dest)] = {'delay': ds, 'dep_type': 'rmt_successor'}
                            
                       
    return nodes, edges
    
            
def odg_generator(n):   
             
    # generate DAG    
    G = digraph_generator(n)
                
    # delays
    delays = {'m': 22, 'a': 2, 'c': 0} 
    
    # generate ODG
    return odg_attr_generator(G, delays)
  

print odg_generator(10)

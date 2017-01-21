from random import shuffle
import time as tm
import numpy as np
import math
import queue

def random_topological_sort_recursive(dag):
  # This is basically taken from networkx's topological_sort_recursive.
  # The differences are: 
  # 1. Randomization of the order we explore node's sucsessors.
  # 2. Removed cycle detection checks.
  def _dfs(v):
    keys=list(dag[v].keys())
    shuffle(list(keys))
    for w in keys:   
        if w not in explored:
            _dfs(w)
    explored.add(v)
    order.append(v)
              
  explored = set()
  order = []

  for v in dag.nodes_iter():
    if v not in explored:
      _dfs(v)

  return list(reversed(order))

def index_dag_sieve(input_spec, dag, index, bound, period_duration):
  # final schedule           
  schedule = []
  
  period_duration
      
  # wild card intensity
  rf_m = 10**4
  rf_a = 10**4
  
  # upper bound on nulls for each wild card
  m_nulls = 2
  a_nulls = 2
  
  # limit on keys of matches rounded to unit_size - match_unit_limit
  match_limit = {}
      
  # concurrent number of packets that can be matched
  concurrent_match_limit = {}
  
  # limit on bits of actions - action_fields_limit
  action_limit = {}
  
  # concurrent number of packets for actions
  concurrent_action_limit = {}
  
  # Init resource usage
  for i in range(period_duration):
      
      # total resources at cycle
      match_limit[i] = 0
      action_limit[i] = 0
      
      # number of different packets
      concurrent_match_limit[i] = []
      concurrent_action_limit[i] = []
      
  # Init time for each node                         
  for i in dag.nodes():
      dag.node[i]['time'] = 0
  
  # topological sort of DAG    
  ts = random_topological_sort_recursive(dag) 
      

  ts_ff_queue = queue.Queue()
  ts_rw_queue = queue.Queue()
          
  for i in ts[index:]:
      ts_ff_queue.put(i)
          
  for i in reversed(ts[:index]):
      ts_rw_queue.put(i)
      
      
  while not (ts_ff_queue.empty() and ts_rw_queue.empty()):
      
      coin = bool(np.random.choice(2))
      
      if ts_ff_queue.empty():
          coin = False
      elif ts_rw_queue.empty():
          coin = True
          
          
      # loop until all nodes are treated            
      if coin:
          
          # exctact nect node in DAG according to topological sort
          curr_node = ts_ff_queue.get()
          
          # the immediate predecessors of the current node                    
          pred = dag.predecessors(curr_node)
                  
          # lower bound on time of current node                
          if pred: 
              time = max([dag.node[i]['time']+\
              dag.edge[i][curr_node]['delay'] for i in pred])
          else:
              time = dag.node[curr_node]['time']
              
          # determine node type            
          MA = dag.node[curr_node]['type']
  
          
          # treat MATCH
          if MA == 'match': 
  
             flag = True
             
             # loop until success
             while flag:
                                                                                                      
                # check resources availability at time%period_duration
                                                                                                      
                match_limit_cond = match_limit[time%period_duration] + \
                math.ceil((1.0 * dag.node[curr_node]['key_width']) / input_spec.match_unit_size)\
                <= input_spec.match_unit_limit
              
                con_match_limit_cond = \
                len(set(concurrent_match_limit[time%period_duration])) < input_spec.match_proc_limit                                                                                      
                
                same_con_match_limit_cond = \
                time in concurrent_match_limit[time%period_duration]
                
                wild_card = np.random.choice(rf_m) > 0
                
                if match_limit_cond and wild_card and \
                (con_match_limit_cond or same_con_match_limit_cond):
  
                    # node time
                    dag.node[curr_node]['time'] = time
                    
                    # update resource usage
                    match_limit[time%period_duration] += \
                    math.ceil((1.0 * dag.node[curr_node]['key_width']) / input_spec.match_unit_size)
                    
                    # update different packet matches at that cycle
                    concurrent_match_limit[time%period_duration].append(time)
                    
                    # add to final schedule
                    schedule.append((curr_node, time))
                    
                    # break loop
                    flag = False
                 
                # coalition or lack of resources 
                else: 
                    
                    if not wild_card:
                        time += np.random.choice(m_nulls)
                        time += 1
                        
                    else:
                        # advance time in case of failure
                        time += 1
                    
                    # in case solution is not feasible
                    if time > bound:
                        return None
                    
                
          # treat Action      
          if MA == 'action': 
              
             flag = True
             
             # loop until success
             while flag:
                                                                      
                # check resources availability at time%period_duration
                                                                      
                action_limit_cond = action_limit[time%period_duration] + \
                dag.node[curr_node]['num_fields'] <= input_spec.action_fields_limit
  
                con_action_limit_cond = \
                len(set(concurrent_action_limit[time%period_duration])) < input_spec.action_proc_limit
                
                same_con_action_limit_cond = \
                time in concurrent_action_limit[time%period_duration]
                
                wild_card = np.random.choice(rf_a) > 0
                                          
                if action_limit_cond and wild_card and \
                (con_action_limit_cond or same_con_action_limit_cond):
                    
                    # node time
                    dag.node[curr_node]['time'] = time
                    
                    # update resource usage
                    action_limit[time%period_duration] += dag.node[curr_node]['num_fields']
                    
                    # update different packet actions at that cycle
                    concurrent_action_limit[time%period_duration].append(time) 
                                              
                    # add to final schedule
                    schedule.append((curr_node, time))
                    
                    # break loop
                    flag = False
                    
                # coalition or lack of resources    
                else:  
  
                    if not wild_card:
                        time += np.random.choice(a_nulls) 
                        time += 1
                        
                    else:
                        # advance time in case of failure
                        time += 1
                   
                    # in case solution is not feasible
                    if time > bound:
                        return None
                           
          
      else:
          
          # exctact nect node in DAG according to topological sort
          curr_node = ts_rw_queue.get()
          
          # the immediate successors of the current node                    
          succ = dag.successors(curr_node)
                  
          # upper bound on time of current node                
          if succ: 
              time = min([dag.node[i]['time']-\
              dag.edge[curr_node][i]['delay'] for i in succ])
          else:
              time = dag.node[curr_node]['time']
              
          # determine node type            
          MA = dag.node[curr_node]['type']
  
          
          # treat MATCH
          if MA == 'match': 
  
             flag = True
             
             # loop until success
             while flag:
                                                                                                      
                # check resources availability at time%period_duration
                                                                                                      
                match_limit_cond = match_limit[time%period_duration] + \
                math.ceil((1.0 * dag.node[curr_node]['key_width']) / input_spec.match_unit_size)\
                <= input_spec.match_unit_limit
              
                con_match_limit_cond = \
                len(set(concurrent_match_limit[time%period_duration])) < input_spec.match_proc_limit                                                                                      
                
                same_con_match_limit_cond = \
                time in concurrent_match_limit[time%period_duration]
                
                wild_card = np.random.choice(rf_m) > 0
                
                if match_limit_cond and wild_card and \
                (con_match_limit_cond or same_con_match_limit_cond):
  
                    # node time
                    dag.node[curr_node]['time'] = time
                    
                    # update resource usage
                    match_limit[time%period_duration] += \
                    math.ceil((1.0 * dag.node[curr_node]['key_width']) / input_spec.match_unit_size)
                    
                    # update different packet matches at that cycle
                    concurrent_match_limit[time%period_duration].append(time)
                    
                    # add to final schedule
                    schedule.append((curr_node, time))
                    
                    # break loop
                    flag = False
                 
                # coalition or lack of resources 
                else: 
                    
                    if not wild_card:
                        time -= np.random.choice(m_nulls)
                        time -= 1
                        
                    else:
                        # advance time in case of failure
                        time -= 1
                    
                    # in case solution is not feasible
                    if time < -bound:
                        return None
                    
                
          # treat Action      
          if MA == 'action': 
              
             flag = True
             
             # loop until success
             while flag:
                                                                      
                # check resources availability at time%period_duration
                                                                      
                action_limit_cond = action_limit[time%period_duration] + \
                dag.node[curr_node]['num_fields'] <= input_spec.action_fields_limit
  
                con_action_limit_cond = \
                len(set(concurrent_action_limit[time%period_duration])) < input_spec.action_proc_limit
                
                same_con_action_limit_cond = \
                time in concurrent_action_limit[time%period_duration]
                
                wild_card = np.random.choice(rf_a) > 0
                                          
                if action_limit_cond and wild_card and \
                (con_action_limit_cond or same_con_action_limit_cond):
                    
                    # node time
                    dag.node[curr_node]['time'] = time
                    
                    # update resource usage
                    action_limit[time%period_duration] += dag.node[curr_node]['num_fields']
                    
                    # update different packet actions at that cycle
                    concurrent_action_limit[time%period_duration].append(time) 
                                              
                    # add to final schedule
                    schedule.append((curr_node, time))
                    
                    # break loop
                    flag = False
                    
                # coalition or lack of resources    
                else:  
  
                    if not wild_card:
                        time -= np.random.choice(a_nulls) 
                        time -= 1
                        
                    else:
                        # advance time in case of failure
                        time -= 1
                   
                    # in case solution is not feasible
                    if time < -bound:
                        return None
                              
  return schedule
    
    
def rnd_sieve(input_spec, dag, time_limit, period_duration):
  star_time = tm.time()
  curr_time = tm.time()
  greedy_initial = {}
  path, delay = dag.critical_path() 
  best = 2 * delay
  best_schedule = None 
  index = 0 

  nodes = dag.number_of_nodes() 
  print ('Looking for greedy feasible solution for %d seconds' % time_limit)
 
  while curr_time - star_time < time_limit:
      schedule = index_dag_sieve(input_spec, dag, index%nodes, 2*delay, period_duration)
      index += 1
      if schedule != None:
          max_val = max([k[1] for k in schedule])
          min_val = min([k[1] for k in schedule])
          if max_val - min_val < best:
              best = max_val - min_val
              best_schedule = schedule
              print ('Found Feasible Solution With Latency', best)
              
      curr_time = tm.time()
  if (best_schedule == None):
    return None

  min_val = min([k[1] for k in best_schedule])
  for i in best_schedule:
    greedy_initial[i[0]] = i[1] - min_val
  return greedy_initial

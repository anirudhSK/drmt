# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import importlib as im
import networkx as nx
import matplotlib.pyplot as plt
import time
import os

from random_odg_generator import odg_generator


# return True if substr is a substring of srt and false otherwise.
def is_substring(srt, substr):    
    return bool(srt.find(substr) >= 0)



def reduce_graph(super_source, fn):
  
    # import operation dependancy graph    
    input_graph = im.import_module(fn, "*")
    
    # retreive nodes and edges   
    nodes = input_graph.nodes
    edges = input_graph.edges
                
    new_nodes = []
    new_edges = []
    
    for node in nodes:
            
        if is_substring(node, 'condition'): 
                   
            input_node = node + '_' +  'input'                     
            output_node = node + '_' +  'output'
            
            cond_true = node + '_' + 'true'
            cond_false = node + '_' + 'false'
    
            new_nodes.append(input_node)                    
            new_nodes.append(output_node)

            new_nodes.append(cond_true)                    
            new_nodes.append(cond_false)
            
            cond_edge = (input_node, output_node)
            
            true_edge = (output_node, cond_true)
            false_edge = (output_node, cond_false)
            
            new_edges.append(cond_edge)
            
            new_edges.append(true_edge)
            new_edges.append(false_edge)
            
        else: 
    
            new_nodes.append(node) 
    
                     
    for edge in edges: 
    
        source, destination = edge           
    
        source_cond = is_substring(source, 'condition') 
        destination_cond = is_substring(destination, 'condition')
                
        if source_cond and destination_cond:
            
            true_false = edges[edge]['condition']
            
            # True
            if true_false:
            
                new_source = source  + '_' + 'true'
                new_destination = destination + '_' + 'input'
                
                new_edge = (new_source, new_destination)        
                new_edges.append(new_edge)
            
            # False    
            else:
                
                new_source = source  + '_' + 'false'
                new_destination = destination + '_' + 'input'
                
                new_edge = (new_source, new_destination)        
                new_edges.append(new_edge)

                
    
        elif source_cond:
          


            true_false = edges[edge]['condition']
            

            # True
            if true_false:
            
                new_source = source  + '_' + 'true'
                
                new_edge = (new_source, destination)        
                new_edges.append(new_edge)
            
            # False    
            else:
                
                new_source = source  + '_' + 'false'
                
                new_edge = (new_source, destination)        
                new_edges.append(new_edge)


            
        elif destination_cond:
    
            new_destination = destination + '_' + 'input'
            
            new_edge = (source, new_destination)        
            new_edges.append(new_edge) 
            
        else:
            
            new_edges.append(edge)
        
    
    new_weighted_edges = []
    
    for edge in new_edges:
        source, destination = edge
        weighted_edge = (source, destination, 1)
        new_weighted_edges.append(weighted_edge)
        
    
    G = nx.DiGraph()
    
    G.add_nodes_from(new_nodes)
    G.add_weighted_edges_from(new_weighted_edges)    
        

    if super_source:  
        
        in_degrees = G.in_degree()
        
        zero_in_degree_nodes = [node for node in in_degrees if in_degrees[node]==0]
        zero_in_degree_nodes_sorted = zero_in_degree_nodes
        zero_in_degree_nodes_sorted.sort()
                
        super_source_node = 'super_source_node'
        super_source_node_edges = []
        
        for zero_in_degree_node in zero_in_degree_nodes: 
            zero_in_degree_weighted_edge = (super_source_node, zero_in_degree_node, 1)
            super_source_node_edges.append(zero_in_degree_weighted_edge)
                    
        G.add_node(super_source_node)
        G.add_weighted_edges_from(super_source_node_edges)
        
        
    
    return G



def main(fn):
    
    # Change to True to create a source to all zero degree nodes.
    super_source = True
    G = reduce_graph(super_source, fn)
    
#     nx.draw(G,pos=nx.random_layout(G),with_labels=True,node_size=1000,iterations=10000)
#     plt.show()
        
    nodes = G.nodes()
    
    super_sink_node = 'super_sink_node'
    
    G.add_node(super_sink_node)
                  
    dep_edges = []
    ancestor_to_descendant = []
     
    # find all descendant-ancestor relations. 
    for node_1 in nodes:
        for node_2 in nodes:            
            if node_1 != node_2:
                if not is_substring(node_1, 'condition') and not is_substring(node_2, 'condition'): 

                    if nx.has_path(G, node_1, node_2):
                        ancestor_to_descendant.append((node_1, node_2))
                        if (node_2, node_1) not in dep_edges:
                            dep_edges.append((node_1, node_2))
                    if nx.has_path(G, node_2, node_1):
                        ancestor_to_descendant.append((node_2, node_1))
                        if (node_2, node_1) not in dep_edges:
                            dep_edges.append((node_1, node_2))
                            

    # for all nodes that do not have descendant-ancestor relations we look for max-flow.                                                                                           
    for node_1 in nodes:
        for node_2 in nodes:
            if not is_substring(node_1, 'condition') and not is_substring(node_2, 'condition'):
                if (node_1, node_2) not in dep_edges and (node_2, node_1) not in dep_edges:
                    if node_1 != node_2 and node_1 != 'super_source_node' and node_2 != 'super_source_node':
                        
                        G.add_weighted_edges_from([(node_1, super_sink_node, 1),(node_2, super_sink_node, 1)]) 
                                                 
                        for curr_source in nodes:
                           if not is_substring(curr_source, 'condition'):
                               if nx.maximum_flow_value(G, curr_source, 'super_sink_node', capacity='weight') == 2:
                                    dep_edges.append((node_1, node_2))
                                    
                                    # make relationship between descendants
                                    for ancestor, descendant in ancestor_to_descendant:
                                        if ancestor == node_1:
                                            if (descendant, node_2) not in dep_edges and (node_2, descendant) not in dep_edges:
                                                dep_edges.append((descendant, node_2))
                                        if ancestor == node_2:
                                            if (descendant, node_1) not in dep_edges and (node_1, descendant) not in dep_edges:
                                                dep_edges.append((descendant, node_1))
                                                
                                    break
                                                               
                        G.remove_edges_from([(node_1, super_sink_node, 1),(node_2, super_sink_node, 1)])
                
                    
    RG = nx.Graph()
    
    RG.add_edges_from(dep_edges) 
    if super_source:
        RG.remove_node('super_source_node')

    # Draw the relation graph.
    # print "\nDrawing the relation graph...\n" 
    # nx.draw(RG,pos=nx.circular_layout(RG),with_labels=True,node_size=1000,iterations=10000)

    N = RG.number_of_nodes()
    print "|V| = %d" % N
    max_num_of_edges = (N*(N-1)) >> 1
    print "0.5(|V|^2 - |V|) = %d" % max_num_of_edges
    E = RG.number_of_edges()
    print "|E| = %d" % E
    unrelated_nodes  = max_num_of_edges - E
    print "Number of unrelated node couples = %d" % unrelated_nodes
    

###############################################################################
###############################################################################      

if __name__ == "__main__":
  
    start_time = time.time()
       
    random_odg = False
    
    if random_odg:
        
        fn = 'test_odg.py'
        
        try:
            os.remove('test_odg.py')
        except OSError:
            pass
        
        print "######################### ODG data - start ########################"
        odg_generator(30, 'test_odg') 
        print "######################### ODG data - end ##########################"
        
    else:
        
        # file name
        fn = 'switch_ingress_sched_data'
        
    
    print "##################### relation graph data - start ##################"
    main(fn) 
    print "##################### relation graph data - end ####################"
           
    print("TIME: --- %s seconds ---" % round(time.time() - start_time, 2))
    
    
       
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

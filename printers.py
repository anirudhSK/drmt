import collections
import math
from functools import *

def timeline_str(objs_at_time, white_space=2, timeslots_per_row=8):
  """ Returns a string representation of the schedule in the
  objs_at_time argument

  Parameters
  ----------
  objs_at_time : dict
      List of objects for each timeslot

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
  assert((type(objs_at_time) is dict) or (type(objs_at_time) is collections.defaultdict))

  # Handle empty dictionary right away
  if not objs_at_time : return 'empty dictionary'

  strs_at_time = dict()
  for time_slot in objs_at_time:
    if type(objs_at_time[time_slot]) is list:
      strs_at_time[time_slot] = [str(o) for o in objs_at_time[time_slot]]
    else:
      strs_at_time[time_slot] = [str(objs_at_time[time_slot])]

  num_strs = sum(len(strs) for strs in strs_at_time.values())
  strlen = max(max(len(s) for s in strs) for strs in strs_at_time.values()) + white_space
  timeline_length = max(t for t in strs_at_time.keys()) + 1
  strlen = max(strlen, len(str(timeline_length))+2)

  K = int(timeline_length / timeslots_per_row)
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

  return timeline

def print_problem(dag, input_spec, match_selector = 'match', action_selector = 'action'):
  cpath, cplat = dag.critical_path()
  print ('# of nodes = ', dag.number_of_nodes())
  print ('# of edges = ', dag.number_of_edges())
  print ('# of matches = ', len(dag.nodes(select='match')))
  print ('# of actions = ', len(dag.nodes(select='action')))
  print ('Match unit size = ', input_spec.match_unit_size)

  match_units = reduce(lambda acc, node: acc + math.ceil((1.0 * dag.node[node]['key_width']) / input_spec.match_unit_size),\
                       dag.nodes(select=match_selector), 0)
  print ('# of match units = ', match_units)
  print ('match_unit_limit = ', input_spec.match_unit_limit)

  max_match_key = reduce(lambda acc, node: max(acc, dag.node[node]['key_width']),dag.nodes(select=match_selector), 0)
  print ('max size of match key in program = ', max_match_key)
  print ('max size of match key in hw = ', input_spec.match_unit_size * input_spec.match_unit_limit)
  if (max_match_key > input_spec.match_unit_size * input_spec.match_unit_limit):
    print ('max match key in program is larger than can be supported by hardware')
    exit(1)

  action_fields = reduce(lambda acc, node: acc + dag.node[node]['num_fields'],\
                       dag.nodes(select=action_selector), 0)
  print ('# of action fields = ', action_fields)
  print ('action_fields_limit = ', input_spec.action_fields_limit)

  max_action_fields = reduce(lambda acc, node: max(acc, dag.node[node]['num_fields']),dag.nodes(select=action_selector), 0)
  print ('max number of action fields in program = ', max_action_fields)
  print ('max number of action fields in hw = ', input_spec.action_fields_limit)
  if (max_action_fields > input_spec.action_fields_limit):
    print ('max number of action fields in program is larger than can be supported by hardware')
    exit(1)

  print ('match_proc_limit =',  input_spec.match_proc_limit)
  print ('action_proc_limit =', input_spec.action_proc_limit)

  print ('Critical path: ', cpath)
  print ('Critical path length = %d cycles' % cplat)

  throughput_upper_bound = \
        min((1.0 * input_spec.action_fields_limit) / action_fields,\
            (1.0 * input_spec.match_unit_limit   ) / match_units)
  print ('Upper bound on throughput = ', throughput_upper_bound)
  return throughput_upper_bound

def print_resource_usage(input_spec, solution):
  print ('Match units usage (max = %d units) on one processor' % input_spec.match_unit_limit)
  print (timeline_str(solution.match_units_usage, white_space=0, timeslots_per_row=16))

  print ('Action fields usage (max = %d fields) on one processor' % input_spec.action_fields_limit)
  print (timeline_str(solution.action_fields_usage, white_space=0, timeslots_per_row=16))

  print ('Match packets (max = %d match packets) on one processor' % input_spec.match_proc_limit)
  print (timeline_str(solution.match_proc_usage, white_space=0, timeslots_per_row=16))

  print ('Action packets (max = %d action packets) on one processor' % input_spec.action_proc_limit)
  print (timeline_str(solution.action_proc_usage, white_space=0, timeslots_per_row=16))

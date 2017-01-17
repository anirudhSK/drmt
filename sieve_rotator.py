# The sieve/rotator algorithm
# Take a coarse PRMT schedule and
# turn it into a DRMT schedule for num_procs processors

class SlotOccupancy:
  def __init__(self):
    self.match_slot = False
    self.action_slot = False

def sieve_rotator(pipe_schedule, num_procs, dM, dA):
  # For each processor is the match, action slot taken already?
  proc_occupied = [SlotOccupancy() for i in range(num_procs)]

  # Current time (starting from 0) after scheduling a certain number of nodes
  # When this is done, current time + 1 gives us the length of the schedule
  current_time = 0

  # Construct drmt schedule as a dictionary
  drmt_schedule = dict()

  for v in pipe_schedule:
    # go through each node in the pipe_schedule
    if v.endswith('TABLE'):

      # schedule match column in table
      while (proc_occupied[current_time%num_procs].match_slot):
        current_time += 1
      drmt_schedule[v.strip('TABLE') + 'MATCH'] = current_time
      proc_occupied[current_time%num_procs].match_slot = True
      current_time += dM

      # schedule action column in table
      while (proc_occupied[current_time%num_procs].action_slot):
        current_time += 1
      drmt_schedule[v.strip('TABLE') + 'ACTION'] = current_time
      proc_occupied[current_time%num_procs].action_slot = True
      current_time += dA

    else:

      assert(v.startswith('_condition') or v.endswith('ACTION'))
      # schedule action column in table, there's no match
      while (proc_occupied[current_time%num_procs].action_slot):
        current_time += 1
      drmt_schedule[v.strip('TABLE') + 'ACTION'] = current_time
      proc_occupied[current_time%num_procs].action_slot = True
      current_time += dA

  return drmt_schedule

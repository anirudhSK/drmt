# The sieve/rotator algorithm
# Take a fine-grained PRMT schedule and
# turn it into a DRMT schedule for period_duration slots

class SlotOccupancy:
  def __init__(self):
    self.match_slot = False
    self.action_slot = False
  def __str__(self):
    return "\nmatch: " + str(self.match_slot) + "\n" + "action: " + str(self.action_slot)
  def __repr__(self):
    return "\nmatch: " + str(self.match_slot) + "\n" + "action: " + str(self.action_slot)

def sieve_rotator(pipe_schedule, period_duration, dM, dA):
  # For each processor is the match, action slot taken already?
  proc_occupied = [SlotOccupancy() for i in range(period_duration)]

  # Current time (starting from 0) after scheduling a certain number of nodes
  current_time = 0

  # Construct drmt schedule as a dictionary
  drmt_schedule = dict()

  # Check that pipeline depth (max_time + 1) is at most half the number of processors
  max_time=max(pipe_schedule)
  #assert((max_time + 1) <= (2 * period_duration)) # otherwise reject it outright

  # Now schedule match and actions alternatively
  for t in range(max_time + 1):
    # schedule match column in table
    if (t%2 == 0):
      termination_counter = 0
      while (proc_occupied[current_time%period_duration].match_slot):
        termination_counter += 1
        if (termination_counter > period_duration):
          print("Can't find a solution in rotator, match const. violated")
          return None
        current_time += 1
#        print ("Incurred one match no-op")
      for v in pipe_schedule[t]: drmt_schedule[v] = current_time
      proc_occupied[current_time%period_duration].match_slot = True
      current_time += dM

    # schedule action column in table
    else:
      termination_counter = 0
      while (proc_occupied[current_time%period_duration].action_slot):
        termination_counter += 1
        if (termination_counter > period_duration):
          print("Can't find a solution in rotator, action const. violated")
          return None
        current_time += 1
#        print ("Incurred one action no-op")
      for v in pipe_schedule[t]: drmt_schedule[v] = current_time
      proc_occupied[current_time%period_duration].action_slot = True
      current_time += dA

  return drmt_schedule

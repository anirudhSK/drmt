import collections
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

    num_strs = sum(len(strs) for strs in strs_at_time.itervalues())
    strlen = max(max(len(s) for s in strs) for strs in strs_at_time.itervalues()) + white_space
    timeline_length = max(t for t in strs_at_time.iterkeys()) + 1
    strlen = max(strlen, len(str(timeline_length))+2)

    K = timeline_length / timeslots_per_row
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

def timeline_str(strs_at_time, white_space=2, timeslots_per_row=8):
    """ Returns a string representation of the schedule in the ops_at_time
        argument

    Parameters
    ----------
    strs_at_time : dict
        List of strings for each timeslot

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

    return (timeline, strlen)

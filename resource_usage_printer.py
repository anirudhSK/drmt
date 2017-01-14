from timeline_printer import timeline_str

def print_resource_usage(input_spec, solution):
    print 'Match units usage (max = %d units) on one processor' % input_spec.match_unit_limit
    print timeline_str(solution.match_units_usage, white_space=0, timeslots_per_row=16)

    print 'Action fields usage (max = %d fields) on one processor' % input_spec.action_fields_limit
    print timeline_str(solution.action_fields_usage, white_space=0, timeslots_per_row=16)

    print 'Match packets (max = %d match packets) on one processor' % input_spec.match_proc_limit
    print timeline_str(solution.match_proc_usage, white_space=0, timeslots_per_row=16)

    print 'Action packets (max = %d action packets) on one processor' % input_spec.action_proc_limit
    print timeline_str(solution.action_proc_usage, white_space=0, timeslots_per_row=16)

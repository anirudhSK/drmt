nodes = \
{'_condition_1': {'type': 'condition', 'ID': 0, 'num_fields': 1},\
 '1_MATCH': {'type': 'match', 'key_width': 640, 'ID': 2},\
 '1_ACTION': {'type': 'action', 'num_fields': 31, 'ID': 3},\
 '2_MATCH': {'type': 'match', 'key_width': 640, 'ID': 4},\
 '2_ACTION': {'type': 'action', 'num_fields': 31, 'ID': 5}}
 
edges = \
{('_condition_1', '1_MATCH'): {'delay': 0, 'dep_type': 'new_match_to_action', 'condition': True},\
 ('_condition_1', '2_MATCH'): {'delay': 0, 'dep_type': 'new_match_to_action', 'condition': True},\
 ('1_MATCH', '1_ACTION'): {'delay': 22, 'dep_type': 'rmt_match'},\
 ('2_MATCH', '2_ACTION'): {'delay': 22, 'dep_type': 'rmt_match'}}

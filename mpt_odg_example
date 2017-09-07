nodes = \
{'_condition_1': {'type': 'condition', 'ID': 0, 'num_fields': 1},\
 '_condition_2': {'type': 'condition', 'ID': 1, 'num_fields': 1},\
 '1_MATCH': {'type': 'match', 'key_width': 320, 'ID': 2},\
 '1_ACTION': {'type': 'action', 'num_fields': 8, 'ID': 3},\
 '2_MATCH': {'type': 'match', 'key_width': 320, 'ID': 4},\
 '2_ACTION': {'type': 'action', 'num_fields': 8, 'ID': 5},\
 '3_MATCH': {'type': 'match', 'key_width': 640, 'ID': 6},\
 '3_ACTION': {'type': 'action', 'num_fields': 8, 'ID': 7},\
 '4_MATCH': {'type': 'match', 'key_width': 640, 'ID': 8},\
 '4_ACTION': {'type': 'action', 'num_fields': 8, 'ID': 9},\
 '5_MATCH': {'type': 'match', 'key_width': 640, 'ID': 10},\
 '5_ACTION': {'type': 'action', 'num_fields': 8, 'ID': 11}}
 
edges = \
{('_condition_1', '1_MATCH'): {'delay': 0, 'dep_type': 'new_match_to_action', 'condition': True},\
 ('_condition_1', '2_MATCH'): {'delay': 0, 'dep_type': 'new_match_to_action', 'condition': True},\
 ('_condition_1', '3_MATCH'): {'delay': 0, 'dep_type': 'new_match_to_action', 'condition': False},\
 ('1_MATCH', '1_ACTION'): {'delay': 22, 'dep_type': 'rmt_match'},\
 ('2_MATCH', '2_ACTION'): {'delay': 22, 'dep_type': 'rmt_match'},\
 ('3_MATCH', '3_ACTION'): {'delay': 22, 'dep_type': 'rmt_match'},\
 ('1_ACTION', '_condition_2'): {'delay': 2, 'dep_type': 'rmt_match'},\
 ('3_ACTION', '5_MATCH'): {'delay': 2, 'dep_type': 'rmt_match'},\
 ('_condition_2', '4_MATCH'): {'delay': 0, 'dep_type': 'new_match_to_action', 'condition': True},\
 ('_condition_2', '5_MATCH'): {'delay': 0, 'dep_type': 'new_match_to_action', 'condition': False},\
 ('4_MATCH', '4_ACTION'): {'delay': 22, 'dep_type': 'rmt_match'},\
 ('5_MATCH', '5_ACTION'): {'delay': 22, 'dep_type': 'rmt_match'}}

 

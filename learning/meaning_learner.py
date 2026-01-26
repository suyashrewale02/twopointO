from db.crud import get_node, create_node, get_or_create_node, create_path, adjust_competing_paths


def learn_definition(subject, definition_text):
    subject_node, _ = get_or_create_node(subject)
    
    create_path(subject, "definition", definition_text)
    
    return subject_node


def learn_relation(subject, relation_type, obj, confidence=1.0):
    subject_node, _ = get_or_create_node(subject)
    obj_node, _ = get_or_create_node(obj)
    
    path = create_path(subject, relation_type, obj, confidence=confidence)
    
    return path


def learn_is_a(subject, category):
    return learn_relation(subject, "is_a", category)


def learn_property(subject, property_name, value, confidence=1.0):
    relation = f"is_{property_name.replace(' ', '_')}"
    return learn_relation(subject, relation, value, confidence)


def correct_relation(subject, relation_type, old_value, new_value):
    adjust_competing_paths(subject, relation_type, new_value)
    
    new_node, _ = get_or_create_node(new_value)
    create_path(subject, relation_type, new_value, confidence=0.5)
    
    return True

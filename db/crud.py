from db.models import Connection, Path, get_session


def get_node(text):
    session = get_session()
    try:
        return session.query(Connection).filter(Connection.connection_text == text.lower()).first()
    finally:
        session.close()


def create_node(text, node_type=None, definition=None):
    session = get_session()
    try:
        existing = get_node(text)
        if existing:
            if (definition and not existing.definition) or (node_type and not existing.type):
                return update_node(text, node_type=node_type if not existing.type else None, 
                                   definition=definition if not existing.definition else None)
            return existing
        node = Connection(
            connection_text=text.lower(),
            type=node_type,
            definition=definition
        )
        session.add(node)
        session.commit()
        session.refresh(node)
        return node
    finally:
        session.close()


def update_node(text, node_type=None, definition=None):
    session = get_session()
    try:
        node = session.query(Connection).filter(Connection.connection_text == text.lower()).first()
        if node:
            if node_type:
                node.type = node_type
            if definition:
                node.definition = definition
            session.commit()
            session.refresh(node)
        return node
    finally:
        session.close()


def get_or_create_node(text, node_type=None, definition=None):
    node = get_node(text)
    if node:
        updated = False
        if definition and not node.definition:
            node = update_node(text, definition=definition)
            updated = True
        if node_type and not node.type:
            node = update_node(text, node_type=node_type)
            updated = True
        return node, False
    return create_node(text, node_type=node_type, definition=definition), True


def get_paths_from(from_text, relation_type=None):
    from sqlalchemy.orm import joinedload
    session = get_session()
    try:
        from_node = get_node(from_text)
        if not from_node:
            return []
        
        query = session.query(Path).options(
            joinedload(Path.from_node),
            joinedload(Path.to_node)
        ).filter(Path.from_connection == from_node.connection_id)
        if relation_type:
            query = query.filter(Path.relation_type == relation_type)
        
        return query.order_by(Path.confidence.desc()).all()
    finally:
        session.close()


def get_path(from_text, relation_type, to_text):
    session = get_session()
    try:
        from_node = get_node(from_text)
        to_node = get_node(to_text)
        if not from_node or not to_node:
            return None
        
        return session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.to_connection == to_node.connection_id,
            Path.relation_type == relation_type
        ).first()
    finally:
        session.close()


def create_path(from_text, relation_type, to_text, confidence=1.0, update_if_higher=False):
    session = get_session()
    try:
        from_node = get_node(from_text)
        to_node = get_node(to_text)
        
        if not from_node:
            from_node = create_node(from_text)
        if not to_node:
            to_node = create_node(to_text)
        
        existing = session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.to_connection == to_node.connection_id,
            Path.relation_type == relation_type
        ).first()
        
        if existing:
            if update_if_higher and confidence > existing.confidence:
                existing.confidence = confidence
                session.commit()
                session.refresh(existing)
            return existing
        
        path = Path(
            from_connection=from_node.connection_id,
            to_connection=to_node.connection_id,
            relation_type=relation_type,
            confidence=confidence
        )
        session.add(path)
        session.commit()
        session.refresh(path)
        return path
    finally:
        session.close()


def update_path_confidence(from_text, relation_type, to_text, new_confidence):
    session = get_session()
    try:
        from_node = get_node(from_text)
        to_node = get_node(to_text)
        if not from_node or not to_node:
            return None
        
        path = session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.to_connection == to_node.connection_id,
            Path.relation_type == relation_type
        ).first()
        
        if path:
            path.confidence = new_confidence
            session.commit()
            return path
        return None
    finally:
        session.close()


def adjust_competing_paths(from_text, relation_type, voted_answer):
    session = get_session()
    try:
        from_node = get_node(from_text)
        if not from_node:
            return
        
        paths = session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.relation_type == relation_type
        ).all()
        
        for path in paths:
            to_node = session.query(Connection).filter_by(connection_id=path.to_connection).first()
            if to_node:
                if to_node.connection_text == voted_answer.lower():
                    path.confidence = min(1.0, path.confidence + 0.1)
                else:
                    path.confidence = max(0.0, path.confidence - 0.1)
        
        session.commit()
    finally:
        session.close()


def get_node_by_id(connection_id):
    session = get_session()
    try:
        return session.query(Connection).filter_by(connection_id=connection_id).first()
    finally:
        session.close()

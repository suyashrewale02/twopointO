from db import Path, get_session
from nodes import get_or_create_node, get_node_by_text


def get_path(from_text, relation_type, to_text=None):
    session = get_session()
    try:
        from_node = get_node_by_text(from_text)
        if not from_node:
            return None
        
        query = session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.relation_type == relation_type
        )
        
        if to_text:
            to_node = get_node_by_text(to_text)
            if not to_node:
                return None
            query = query.filter(Path.to_connection == to_node.connection_id)
        
        return query.all()
    finally:
        session.close()


def get_best_answer(from_text, relation_type):
    session = get_session()
    try:
        from_node = get_node_by_text(from_text)
        if not from_node:
            return None, None
        
        paths = session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.relation_type == relation_type
        ).order_by(Path.confidence.desc()).all()
        
        if not paths:
            return None, None
        
        best_path = paths[0]
        to_node = session.query(from_node.__class__).filter_by(connection_id=best_path.to_connection).first()
        
        return to_node.connection_text if to_node else None, best_path.confidence
    finally:
        session.close()


def create_path(from_text, relation_type, to_text, confidence=1.0):
    session = get_session()
    try:
        from_node = get_or_create_node(from_text)
        to_node = get_or_create_node(to_text, node_type="boolean" if to_text in ["yes", "no"] else None)
        
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


def update_confidence(from_text, relation_type, to_text, new_vote):
    session = get_session()
    try:
        from_node = get_node_by_text(from_text)
        to_node = get_node_by_text(to_text)
        
        if not from_node or not to_node:
            return None
        
        path = session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.to_connection == to_node.connection_id,
            Path.relation_type == relation_type
        ).first()
        
        if path:
            current_conf = path.confidence
            total_votes = 1 / current_conf if current_conf > 0 else 1
            new_total = total_votes + 1
            path.confidence = (current_conf * total_votes + new_vote) / new_total
            session.commit()
            return path.confidence
        return None
    finally:
        session.close()


def adjust_competing_confidences(from_text, relation_type, voted_answer):
    session = get_session()
    try:
        from_node = get_node_by_text(from_text)
        if not from_node:
            return
        
        paths = session.query(Path).filter(
            Path.from_connection == from_node.connection_id,
            Path.relation_type == relation_type
        ).all()
        
        total_paths = len(paths)
        if total_paths == 0:
            return
        
        for path in paths:
            to_node = session.query(from_node.__class__).filter_by(connection_id=path.to_connection).first()
            if to_node:
                current_conf = path.confidence
                if to_node.connection_text == voted_answer:
                    path.confidence = min(1.0, current_conf + 0.1)
                else:
                    path.confidence = max(0.0, current_conf - 0.1)
        
        session.commit()
    finally:
        session.close()

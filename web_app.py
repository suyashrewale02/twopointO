import sys
import io
from contextlib import redirect_stdout
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import asyncio
import uvicorn

sys.path.insert(0, '.')

from db.models import init_db
from db.crud import get_node, create_path, get_or_create_node
from learning.word_learner import learn_word_deep
from learning.grammar_learner import detect_pattern, init_grammar_patterns
from reasoning.parser import tokenize
from reasoning.graph_traversal import traverse, traverse_deep
from reasoning.answer_builder import build_answer, format_paths

app = FastAPI(title="Knowledge Graph Chat")

class ChatMessage(BaseModel):
    message: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_log(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_json({"type": "log", "content": message})
            except:
                pass

    async def send_response(self, websocket: WebSocket, message: str):
        await websocket.send_json({"type": "response", "content": message})

manager = ConnectionManager()

pending_learning = {}

async def process_query_web(query, log_callback, session_id=None):
    """Process query and stream logs in real-time"""
    logs = []
    
    async def log(msg):
        logs.append(msg)
        await log_callback(msg)
    
    await log(f"\n{'='*50}")
    await log(f'STEP 1 — Receive Query: "{query}"')
    
    tokens = tokenize(query)
    await log(f"\nSTEP 2 — Tokenize:")
    await log(f"  Tokens: {tokens}")
    
    await log(f"\nSTEP 3 — Word-Level Node Check:")
    await log(f"  {'Word':<15} {'Exists?':<10} {'Action':<15} {'Source'}")
    await log(f"  {'-'*55}")
    
    for token in tokens:
        existing = get_node(token)
        if existing:
            await log(f"  {token:<15} {'✓':<10} {'skip':<15} database")
        else:
            node, created, source, connections = learn_word_deep(token, max_depth=2)
            if created:
                await log(f"  {token:<15} {'✗':<10} {'learned':<15} {source}")
                if node and node.definition:
                    await log(f"    → {node.type}: {node.definition[:60]}...")
                if len(connections) > 0:
                    await log(f"    → Deep connections: {len(connections)}")
            elif node:
                await log(f"  {token:<15} {'✓':<10} {'exists':<15} {source}")
        await asyncio.sleep(0)  # Allow WebSocket to send
    
    await log(f"\nSTEP 4 — Grammar Recognition:")
    pattern_info = detect_pattern(tokens)
    
    response = ""
    
    if pattern_info:
        await log(f"  Pattern: {pattern_info['pattern']}")
        await log(f"  Type: {pattern_info['type']}")
        await log(f"  Expects: {pattern_info.get('expects', 'N/A')}")
        
        if pattern_info["type"] == "learned_response":
            await log(f"\nSTEP 5 — Learned Pattern Recognized:")
            await log(f"  Pattern: {pattern_info.get('pattern_key', '')}")
            await log(f"  Type: {pattern_info.get('response_type', 'learned')}")
            response = pattern_info.get('response', '')
            await log(f"\nResponse: {response}")
        
        elif pattern_info["type"] == "definition_query":
            subject = pattern_info["subject"]
            await log(f"\nSTEP 5 — Looking up '{subject}':")
            
            node = get_node(subject)
            paths = traverse(subject, max_depth=5)
            
            if node and node.definition:
                response = f"{subject.capitalize()}: {node.definition}"
                await log(f"  Found definition")
            else:
                response = f"I don't know about '{subject}' yet."
            await log(f"\nResponse: {response}")
        
        elif pattern_info["type"] == "property_of_query":
            property_name = pattern_info["property"]
            entity = pattern_info["entity"]
            await log(f"\nSTEP 5 — Looking for '{property_name}' of '{entity}':")
            
            paths = traverse(entity, max_depth=5)
            property_paths = [p for p in paths if property_name in p.get("relation", "") or property_name in p.get("to", "")]
            
            if property_paths:
                await log(f"  Found {len(property_paths)} relevant paths")
                response = f"{entity} → {property_paths[0]['relation']} → {property_paths[0]['to']}"
            else:
                response = f"I don't know the {property_name} of {entity}."
            await log(f"\nResponse: {response}")
        
        elif pattern_info["type"] == "inferred_query":
            intent = pattern_info.get("intent", "unknown")
            focus = pattern_info.get("focus", "")
            tokens = pattern_info.get("tokens", [])
            await log(f"\nSTEP 5 — Intent Inference:")
            await log(f"  Inferred intent: {intent}")
            await log(f"  Focus word: '{focus}'")
            
            if intent == "greeting":
                pattern_key = " ".join(tokens) if tokens else focus
                if session_id:
                    pending_learning[session_id] = {
                        "type": "greeting",
                        "pattern_key": pattern_key,
                        "focus": focus
                    }
                response = f"This looks like a greeting! How should I respond to '{focus}'? (Type your response)"
            else:
                response = f"I'm trying to understand what you mean by this."
            await log(f"\nResponse: {response}")
        
        else:
            response = "I understood the pattern but don't know how to respond yet."
            await log(f"\nResponse: {response}")
    else:
        await log(f"  No pattern recognized.")
        response = "I don't recognize this pattern. Can you teach me?"
        await log(f"\nResponse: {response}")
    
    return response, logs

@app.on_event("startup")
async def startup():
    print("Initializing database...")
    init_db()
    init_grammar_patterns()
    print("Knowledge Graph Ready.")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    session_id = id(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                query = data.get("content", "")
                
                if session_id in pending_learning:
                    learning = pending_learning[session_id]
                    if learning["type"] == "greeting":
                        pattern_key = learning["pattern_key"]
                        response_text = query
                        
                        get_or_create_node(pattern_key, node_type="learned_pattern")
                        get_or_create_node(response_text, node_type="response")
                        create_path(pattern_key, "responds_with", response_text, confidence=1.0)
                        create_path(pattern_key, "pattern_type", "greeting", confidence=1.0)
                        
                        await manager.broadcast_log(f"\n  Learning: '{pattern_key}' → responds_with → '{response_text}'")
                        await manager.send_response(websocket, f"Learned! I'll respond to '{learning['focus']}' with '{response_text}'")
                        
                        del pending_learning[session_id]
                        continue
                
                async def stream_log(msg):
                    await manager.broadcast_log(msg)
                
                response, logs = await process_query_web(query, stream_log, session_id)
                
                await manager.send_response(websocket, response)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if session_id in pending_learning:
            del pending_learning[session_id]

if __name__ == "__main__":
    import os
    os.makedirs("static", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)

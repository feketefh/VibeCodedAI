# jarvis_logic.py
# Enhanced with Ollama, streaming, user-defined rules, and internet access
import json
import os
import yaml
import re
from pathlib import Path
from datetime import datetime

# ------------------ Ollama Import ------------------
OLLAMA_AVAILABLE = False
try:
    import ollama
    OLLAMA_AVAILABLE = True
    print("✓ Ollama loaded")
except Exception as e:
    print(f"⚠ Ollama not available: {e}")
    print("Install with: pip install ollama")
    print("And install Ollama from: https://ollama.ai")

# ------------------ Web Search Import ------------------
WEB_SEARCH_AVAILABLE = False
try:
    from duckduckgo_search import DDGS
    WEB_SEARCH_AVAILABLE = True
    print("✓ DuckDuckGo search loaded")
except Exception as e:
    print(f"⚠ Web search not available: {e}")
    print("Install with: pip install duckduckgo-search")

# ------------------ Fallback AI Models ------------------
GPT4ALL_AVAILABLE = False
try:
    from gpt4all import GPT4All
    GPT4ALL_AVAILABLE = True
    print("✓ GPT4All available as fallback")
except:
    pass

SENTIMENT_AVAILABLE = False
try:
    from transformers import pipeline
    sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    SENTIMENT_AVAILABLE = True
    print("✓ Sentiment Analysis loaded")
except:
    pass

# ------------------ Configuration ------------------
DATA_DIR = Path("jarvis_full_data")
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.yaml"
HISTORY_FILE = DATA_DIR / "chat_history.json"
LOG_FILE = DATA_DIR / "logic_memory.json"
CONTEXT_FILE = DATA_DIR / "conversation_context.json"

MAX_SEARCH_RETRIES = 3

# ------------------ Default Configuration ------------------
DEFAULT_CONFIG = {
    "model": "llama3.2",
    "rules": """You are JARVIS, an advanced AI assistant created for a personal computer system.

Rules:
- You are intelligent, helpful, and concise
- Follow only what is written in these rules
- You may request internet searches by writing: SEARCH("query")
- When you need current information, always use SEARCH()
- Keep responses natural and informative
- You can control 3D rendering, security systems, and computer vision
- Respond in Hungarian when the user speaks Hungarian, otherwise in English
- If you need more information, ask to search again
- Be professional but friendly, like Tony Stark's JARVIS

Capabilities you can reference:
- 3D material generation (Titanium, Gold, Steel, Copper, Glass, etc.)
- Security and firewall management
- Computer vision and object detection
- Time, date, and system information
- Web search for current information""",
    "temperature": 0.7,
    "stream": True,
    "max_tokens": 500
}

# ------------------ Load/Save Config ------------------
def load_config():
    """Load configuration from YAML file"""
    if not CONFIG_FILE.exists():
        print("📝 Creating default config.yaml...")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        print(f"✓ Config loaded: Model={config.get('model', 'llama3.2')}")
        return config
    except Exception as e:
        print(f"⚠ Config load error: {e}, using defaults")
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to YAML file"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        print("✓ Config saved")
    except Exception as e:
        print(f"⚠ Config save error: {e}")

# ------------------ Chat History Management ------------------
def load_history():
    """Load chat history from JSON"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ History load error: {e}")
    
    # Return default with system rules
    config = load_config()
    return [{"role": "system", "content": config.get("rules", DEFAULT_CONFIG["rules"])}]

def save_history(history):
    """Save chat history to JSON"""
    try:
        # Keep only last 50 messages
        history = history[:1] + history[-49:]  # Keep system message + last 49
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ History save error: {e}")

def clear_history():
    """Clear chat history and start fresh"""
    config = load_config()
    history = [{"role": "system", "content": config.get("rules", DEFAULT_CONFIG["rules"])}]
    save_history(history)
    print("✓ Chat history cleared")
    return history

# ------------------ Context Management ------------------
def load_context():
    """Load conversation context"""
    try:
        if CONTEXT_FILE.exists():
            with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"user_name": None, "preferences": {}, "last_topics": []}

def save_context(context):
    """Save conversation context"""
    try:
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(context, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Context save error: {e}")

# ------------------ Web Search Function ------------------
def web_search(query, retries=MAX_SEARCH_RETRIES):
    """Search the web using DuckDuckGo with automatic retries"""
    if not WEB_SEARCH_AVAILABLE:
        return "Web search not available. Install: pip install duckduckgo-search"
    
    print(f"\n🔎 Searching the web for: {query}")
    results_text = ""
    
    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            
            if not results:
                print(f"⚠️ No results found, retrying... ({attempt + 1}/{retries})")
                continue
            
            for r in results:
                results_text += f"- {r['title']}: {r['body']}\n  URL: {r['href']}\n\n"
            
            if results_text.strip():
                print("✅ Found results.")
                return results_text
                
        except Exception as e:
            print(f"⚠️ Search attempt {attempt + 1} failed: {e}")
    
    print("❌ No useful results found after retries.")
    return "No relevant information found online."

# ------------------ Ollama Chat Function ------------------
def chat_with_ollama(user_input, history, config, stream_callback=None):
    """
    Chat with Ollama model with streaming support
    
    Args:
        user_input: User's message
        history: Chat history
        config: Configuration dict
        stream_callback: Optional callback function for streaming (receives text chunks)
    
    Returns:
        response_text: Complete response from the model
    """
    if not OLLAMA_AVAILABLE:
        return "Ollama not available. Install from: https://ollama.ai"
    
    # Add user message to history
    history.append({"role": "user", "content": user_input})
    
    response_text = ""
    model_name = config.get("model", "llama3.2")
    
    try:
        # Stream the response
        for chunk in ollama.chat(
            model=model_name,
            messages=history,
            stream=True
        ):
            if chunk.get("message") and chunk["message"].get("content"):
                content = chunk["message"]["content"]
                response_text += content
                
                # Call the callback if provided (for UI updates)
                if stream_callback:
                    stream_callback(content)
        
        # Check if model requested a web search
        if "SEARCH(" in response_text.upper():
            query_matches = re.findall(r'SEARCH\(["\'](.+?)["\']\)', response_text, re.IGNORECASE)
            
            if query_matches:
                query = query_matches[-1]  # Take last search request
                search_results = web_search(query)
                
                # Add search results to history
                history.append({"role": "assistant", "content": response_text})
                history.append({
                    "role": "system", 
                    "content": f"[Web search results for '{query}']:\n{search_results}"
                })
                
                # Get model to summarize/use the results
                print("\n🤖 Processing search results...")
                if stream_callback:
                    stream_callback("\n[Processing search results...]\n")
                
                response_text = ""
                for chunk in ollama.chat(
                    model=model_name,
                    messages=history,
                    stream=True
                ):
                    if chunk.get("message") and chunk["message"].get("content"):
                        content = chunk["message"]["content"]
                        response_text += content
                        if stream_callback:
                            stream_callback(content)
        
        # Add final response to history
        history.append({"role": "assistant", "content": response_text})
        
        return response_text
        
    except Exception as e:
        error_msg = f"Ollama error: {e}"
        print(f"❌ {error_msg}")
        return error_msg

# ------------------ Fallback Decision Making ------------------
def fallback_decision(input_text):
    """Fallback logic when Ollama is not available"""
    input_lower = input_text.lower()
    
    # Basic responses
    if any(word in input_lower for word in ["hello", "szia", "hi", "helló", "üdv"]):
        return "Szia! Én vagyok JARVIS. Miben segíthetek?"
    
    elif "idő" in input_lower or "óra" in input_lower:
        return f"A pontos idő: {datetime.now().strftime('%H:%M:%S')}"
    
    elif "dátum" in input_lower or "nap" in input_lower:
        return f"A mai dátum: {datetime.now().strftime('%Y-%m-%d')}"
    
    elif "ki vagy" in input_lower or "név" in input_lower:
        return "Én vagyok JARVIS, egy mesterséges intelligencia asszisztens."
    
    elif any(word in input_lower for word in ["3d", "modell", "anyag"]):
        return "Elindítom a 3D anyag generálást. Milyen anyagot szeretnél?"
    
    # Try GPT4All if available
    elif GPT4ALL_AVAILABLE:
        try:
            llm = GPT4All("orca-mini-3b-gguf2-q4_0.gguf")
            prompt = f"You are JARVIS. Respond to: {input_text}\nKeep it concise:"
            return llm.generate(prompt, max_tokens=150)
        except:
            pass
    
    return "Sajnálom, jelenleg korlátozott módban működöm. Telepítsd az Ollama-t a teljes funkcionalitáshoz: https://ollama.ai"

# ------------------ Main Decision Function ------------------
def decide_action(input_text, stream_callback=None):
    """
    Main decision making function with Ollama + streaming + web search
    
    Args:
        input_text: User input
        stream_callback: Optional callback for streaming responses
    
    Returns:
        response: AI response
    """
    # Load config and history
    config = load_config()
    history = load_history()
    context = load_context()
    
    # Analyze sentiment if available
    sentiment_data = None
    if SENTIMENT_AVAILABLE:
        try:
            sentiment = sentiment_analyzer(input_text)[0]
            sentiment_data = sentiment
        except:
            pass
    
    # Use Ollama if available
    if OLLAMA_AVAILABLE:
        response = chat_with_ollama(input_text, history, config, stream_callback)
    else:
        response = fallback_decision(input_text)
        history.append({"role": "user", "content": input_text})
        history.append({"role": "assistant", "content": response})
    
    # Save history
    save_history(history)
    
    # Update context
    context["last_topics"].append(input_text[:50])
    context["last_topics"] = context["last_topics"][-5:]
    save_context(context)
    
    # Log to memory
    log_interaction(input_text, response, sentiment_data)
    
    return response

# ------------------ Memory Logging ------------------
def log_interaction(input_text, response, sentiment=None):
    """Log interaction to memory file"""
    try:
        memory = []
        if LOG_FILE.exists():
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                memory = json.load(f)
        
        memory.append({
            "time": datetime.utcnow().isoformat(),
            "input": input_text,
            "response": response[:200] + "..." if len(response) > 200 else response,
            "sentiment": sentiment,
            "ai_type": "ollama" if OLLAMA_AVAILABLE else "fallback"
        })
        
        # Keep only last 100 entries
        memory = memory[-100:]
        
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Memory log error: {e}")

# ------------------ Scene Analysis ------------------
def analyze_scene(scene_data=None):
    """Enhanced scene analysis"""
    analysis = {
        "objects_detected": [],
        "threat_level": 0,
        "description": ""
    }
    
    if scene_data:
        objects = scene_data.get("objects", [])
        analysis["objects_detected"] = objects
        
        # Calculate threat level
        dangerous_objects = ["knife", "gun", "fire", "weapon"]
        threat_count = sum(1 for obj in objects if any(danger in obj.lower() for danger in dangerous_objects))
        analysis["threat_level"] = min(threat_count * 3, 10)
        
        # Generate description with Ollama if available
        if OLLAMA_AVAILABLE and objects:
            try:
                prompt = f"Describe this scene briefly: {', '.join(objects[:5])}"
                config = load_config()
                response = ollama.generate(
                    model=config.get("model", "llama3.2"),
                    prompt=prompt
                )
                analysis["description"] = response["response"]
            except:
                analysis["description"] = f"Scene contains: {', '.join(objects[:5])}"
        else:
            analysis["description"] = f"Detected {len(objects)} objects"
    
    return analysis

# ------------------ Get AI Status ------------------
def get_ai_status():
    """Returns which AI systems are available"""
    return {
        "ollama": OLLAMA_AVAILABLE,
        "web_search": WEB_SEARCH_AVAILABLE,
        "gpt4all_fallback": GPT4ALL_AVAILABLE,
        "sentiment_analysis": SENTIMENT_AVAILABLE,
        "streaming": OLLAMA_AVAILABLE,
        "internet_access": WEB_SEARCH_AVAILABLE
    }

# ------------------ Test/CLI Mode ------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("JARVIS AI Enhanced Logic with Ollama")
    print("="*60 + "\n")
    
    # Show AI status
    status = get_ai_status()
    print("AI Systems Status:")
    for system, available in status.items():
        print(f"  {'✓' if available else '✗'} {system}")
    print()
    
    if not OLLAMA_AVAILABLE:
        print("⚠️ Ollama not detected!")
        print("Install from: https://ollama.ai")
        print("Then run: ollama pull llama3.2")
        print()
    
    # Load config
    config = load_config()
    print(f"Model: {config.get('model', 'llama3.2')}")
    print(f"Type 'exit' to quit, 'clear' to reset chat, 'config' to edit rules\n")
    print("="*60 + "\n")
    
    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == "clear":
                clear_history()
                continue
            
            if user_input.lower() == "config":
                print(f"\nCurrent config file: {CONFIG_FILE}")
                print("Edit config.yaml to change model and rules")
                continue
            
            print("JARVIS: ", end="", flush=True)
            
            # Stream callback for real-time output
            def print_stream(text):
                print(text, end="", flush=True)
            
            response = decide_action(user_input, stream_callback=print_stream)
            print("\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
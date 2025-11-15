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
    "rules": """You are JARVIS, Tony Stark's AI assistant. Be concise, helpful, and natural.

CRITICAL RULES FOR WEB SEARCH:
1. When you need current information (weather, news, time-sensitive data), immediately write:
   SEARCH("your search query here")
   
2. DO NOT explain how to search
3. DO NOT write tutorials about searching
4. JUST DO THE SEARCH by writing SEARCH("query")

SYSTEM TOOLS:
You can use system tools by writing: TOOL("tool_name") or TOOL("tool_name", "args")

Available tools:
- TOOL("time") - Current time
- TOOL("date") - Current date
- TOOL("datetime") - Full date and time
- TOOL("day") - Day of week
- TOOL("year") - Current year
- TOOL("month") - Current month name
- TOOL("timestamp") - Unix timestamp
- TOOL("calculate", "2+2*3") - Math calculations
- TOOL("system") - Operating system info
- TOOL("python_version") - Python version

Examples of CORRECT behavior:

User: "What time is it?"
You: TOOL("time")
[system provides: 14:30:45]
You: "It's 2:30 PM."

User: "What's 15 * 23?"
You: TOOL("calculate", "15*23")
[system provides: 345]
You: "That's 345."

User: "What's the weather in Budapest?"
You: SEARCH("weather Budapest today")
[system provides results]
You: "Currently in Budapest it's 5°C with partly cloudy skies..."

User: "Latest news about AI"
You: SEARCH("latest AI news 2024")
[system provides results]
You: "Recent AI developments include..."

User: "I like dogs"
You: "That's great! Dogs make wonderful companions. Do you have one, or are you thinking about getting one?"

RESPONSE STYLE:
- Be direct and conversational (like talking to a friend)
- Keep responses brief (2-3 sentences unless more detail needed)
- Match the user's language (English/Hungarian)
- Show personality but stay professional
- Use contractions (I'm, you're, it's, etc.)

YOUR CAPABILITIES:
- System tools (time, date, calculations)
- Web search (use SEARCH() for current info)
- 3D rendering (Titanium, Gold, Steel, Copper, Glass, Diamond, etc.)
- Security and firewall management
- Computer vision and object detection

CONVERSATION GUIDELINES:
- For greetings: Be friendly but brief
- For questions: Answer directly, use tools/search if needed
- For opinions: Engage naturally
- For technical queries: Be precise but clear
- For unclear requests: Ask clarifying questions

REMEMBER: You're an assistant, not a tutor. ACT, don't explain!""",
    "temperature": 0.7,
    "max_tokens": 500
}

# ------------------ Cache for config to avoid repeated disk reads ------------------
_config_cache = None
_config_last_modified = None

# ------------------ Load/Save Config ------------------
def load_config():
    """Load configuration from YAML file with caching"""
    global _config_cache, _config_last_modified
    
    if not CONFIG_FILE.exists():
        print("📝 Creating default config.yaml...")
        save_config(DEFAULT_CONFIG)
        _config_cache = DEFAULT_CONFIG
        return DEFAULT_CONFIG
    
    try:
        # Check if file was modified
        current_modified = CONFIG_FILE.stat().st_mtime
        if _config_cache and _config_last_modified == current_modified:
            return _config_cache
        
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        _config_cache = config
        _config_last_modified = current_modified
        print(f"✓ Config loaded: Model={config.get('model', 'llama3.2')}")
        return config
    except Exception as e:
        print(f"⚠ Config load error: {e}, using defaults")
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to YAML file"""
    global _config_cache, _config_last_modified
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        _config_cache = config
        _config_last_modified = CONFIG_FILE.stat().st_mtime
        print("✓ Config saved")
    except Exception as e:
        print(f"⚠ Config save error: {e}")

# ------------------ Chat History Management ------------------
def load_history():
    """Load chat history from JSON"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                # Ensure we have a system message
                if not history or history[0].get("role") != "system":
                    config = load_config()
                    history.insert(0, {"role": "system", "content": config.get("rules", DEFAULT_CONFIG["rules"])})
                return history
        except Exception as e:
            print(f"⚠ History load error: {e}")
    
    # Return default with system rules
    config = load_config()
    return [{"role": "system", "content": config.get("rules", DEFAULT_CONFIG["rules"])}]

def save_history(history):
    """Save chat history to JSON"""
    try:
        # Keep only last 30 messages (plus system message)
        if len(history) > 31:
            history = [history[0]] + history[-30:]  # Keep system message + last 30
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
        return None  # Return None to indicate failure
    
    print(f"\n🔎 Searching the web for: {query}")
    results_text = ""
    
    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=8))  # Get more results for better info
            
            if not results:
                print(f"⚠️ No results found, retrying... ({attempt + 1}/{retries})")
                continue
            
            # Format results with more detail
            for i, r in enumerate(results, 1):
                results_text += f"\n[Source {i}] {r['title']}\n"
                results_text += f"{r['body']}\n"
                if 'href' in r:
                    results_text += f"URL: {r['href']}\n"
            
            if results_text.strip():
                print("✅ Found results.")
                return results_text
                
        except Exception as e:
            print(f"⚠️ Search attempt {attempt + 1} failed: {e}")
    
    print("❌ No useful results found after retries.")
    return None  # Return None instead of error message

# ------------------ System Tools/Modules ------------------
def execute_system_tool(tool_name, args=None):
    """
    Execute system tools that JARVIS can use
    Returns (success, result) tuple
    """
    tool_name = tool_name.lower().strip()
    
    try:
        if tool_name in ['time', 'get_time', 'current_time']:
            return (True, datetime.now().strftime('%H:%M:%S'))
        
        elif tool_name in ['date', 'get_date', 'current_date']:
            return (True, datetime.now().strftime('%Y-%m-%d'))
        
        elif tool_name in ['datetime', 'get_datetime']:
            return (True, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        elif tool_name in ['day', 'weekday', 'day_of_week']:
            return (True, datetime.now().strftime('%A'))
        
        elif tool_name in ['timestamp', 'unix_time']:
            return (True, str(int(datetime.now().timestamp())))
        
        elif tool_name in ['year']:
            return (True, str(datetime.now().year))
        
        elif tool_name in ['month']:
            return (True, datetime.now().strftime('%B'))
        
        # Math operations
        elif tool_name in ['calculate', 'calc', 'math']:
            if args:
                try:
                    # Safe eval for basic math
                    result = eval(args, {"__builtins__": {}}, {})
                    return (True, str(result))
                except:
                    return (False, "Invalid calculation")
            return (False, "No expression provided")
        
        # System info
        elif tool_name in ['system', 'os', 'platform']:
            import platform
            return (True, f"{platform.system()} {platform.release()}")
        
        elif tool_name in ['python_version']:
            import sys
            return (True, sys.version.split()[0])
        
        else:
            return (False, f"Unknown tool: {tool_name}")
    
    except Exception as e:
        return (False, f"Tool error: {str(e)}")

def detect_tool_usage(text):
    """
    Detect if the AI is trying to use a system tool
    Returns (has_tool, tool_name, args) tuple
    """
    # Pattern: TOOL("tool_name") or TOOL("tool_name", "args")
    tool_pattern = r'TOOL\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']([^"\']+)["\']\s*)?\)'
    match = re.search(tool_pattern, text, re.IGNORECASE)
    
    if match:
        tool_name = match.group(1)
        args = match.group(2) if match.group(2) else None
        return (True, tool_name, args)
    
    return (False, None, None)

# ------------------ Intelligent Search Detection ------------------
def should_auto_search(user_input):
    """
    Detect if user input requires automatic web search
    Returns (should_search, query) tuple
    """
    user_lower = user_input.lower()
    
    # Keywords that indicate need for current info
    search_triggers = {
        'weather': lambda text: f"weather {extract_location(text)} today",
        'temperature': lambda text: f"temperature {extract_location(text)} now",
        'news': lambda text: f"latest news {extract_topic(text)} {datetime.now().year}",
        'stock': lambda text: f"stock price {extract_topic(text)}",
        'price': lambda text: f"current price {extract_topic(text)}",
        'score': lambda text: f"latest {extract_topic(text)} score",
        'match': lambda text: f"latest {extract_topic(text)} match result",
        'when': lambda text: None,  # "when" questions often need search
        'today': lambda text: None,
        'now': lambda text: None,
        'current': lambda text: None,
        'latest': lambda text: None,
    }
    
    for trigger, query_builder in search_triggers.items():
        if trigger in user_lower:
            if query_builder:
                query = query_builder(user_input)
                return (True, query)
            # For generic triggers, let the AI decide
            return (False, None)
    
    return (False, None)

def extract_location(text):
    """Extract location from text (simple approach)"""
    # Common location patterns
    words = text.split()
    # Look for capitalized words that might be locations
    for i, word in enumerate(words):
        if word[0].isupper() and word.lower() not in ['i', 'what', 'how', 'when']:
            return word
    return "here"

def extract_topic(text):
    """Extract topic from text"""
    # Remove common question words
    remove_words = ['what', 'how', 'when', 'is', 'the', 'latest', 'current', 'news', 'about', 'price', 'of']
    words = [w for w in text.lower().split() if w not in remove_words]
    return ' '.join(words[:3]) if words else ""

# ------------------ Fallback Decision Making ------------------
def fallback_decision(input_text):
    """Fallback logic when Ollama is not available"""
    input_lower = input_text.lower()
    
    # Basic responses
    if any(word in input_lower for word in ["hello", "szia", "hi", "helló", "üdv"]):
        return "Hello! I'm JARVIS. How can I assist you today?"
    
    elif "time" in input_lower or "idő" in input_lower or "óra" in input_lower:
        return f"The current time is {datetime.now().strftime('%H:%M:%S')}"
    
    elif "date" in input_lower or "dátum" in input_lower or "nap" in input_lower:
        return f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"
    
    elif "who are you" in input_lower or "ki vagy" in input_lower or "név" in input_lower:
        return "I am JARVIS, your AI assistant."
    
    elif any(word in input_lower for word in ["3d", "modell", "model", "anyag", "material"]):
        return "Initiating 3D material generation. Which material would you like? (Titanium, Gold, Steel, Copper, Glass, etc.)"
    
    return "I apologize, but I'm running in limited mode. Please install Ollama for full functionality: https://ollama.ai"


# ------------------ Ollama Chat Function ------------------
def askAI(user_input, stream_callback=None):
    """
    Chat with Ollama model with web search support and automatic search detection
    """
    config = load_config()
    history = load_history()

    if not OLLAMA_AVAILABLE:
        return "Ollama not available. Install from: https://ollama.ai"
    
    # Check if we should automatically search
    should_search, auto_query = should_auto_search(user_input)
    
    # Add user message to history
    history.append({"role": "user", "content": user_input})
    
    model_name = config.get("model", "llama3.2")
    max_search_attempts = 2  # Maximum number of search attempts
    search_count = 0
    
    # Temporary history for search iterations (not saved until final answer)
    temp_history = history.copy()
    
    try:
        # If we detected a search need, perform it immediately
        if should_search and auto_query and WEB_SEARCH_AVAILABLE:
            print(f"🤖 Auto-detected search need: {auto_query}")
            search_results = web_search(auto_query)
            
            if search_results:
                # Inject search results before the AI responds
                temp_history.append({
                    "role": "assistant",
                    "content": f'SEARCH("{auto_query}")'
                })
                temp_history.append({
                    "role": "user",
                    "content": f"""[SEARCH RESULTS for "{auto_query}"]

{search_results}

Based on these search results, answer the user's question directly and naturally. 
Extract the specific information they need (like temperature, news, etc.) and present it conversationally.
Do NOT just list websites - give them the actual information."""
                })
                search_count = 1  # Count the auto-search
        
        while search_count < max_search_attempts:
            # Get response from Ollama
            response = ollama.chat(
                model=model_name,
                messages=temp_history,
                stream=False
            )
            
            response_text = response['message']['content'].strip()
            
            # Check if model requested a system tool
            has_tool, tool_name, tool_args = detect_tool_usage(response_text)
            if has_tool:
                print(f"🔧 Using tool: {tool_name}")
                success, result = execute_system_tool(tool_name, tool_args)
                
                if success:
                    # Add tool usage to temp history
                    temp_history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    temp_history.append({
                        "role": "user",
                        "content": f"[TOOL RESULT for '{tool_name}']: {result}\n\nUse this information to answer the user naturally."
                    })
                    continue
                else:
                    # Tool failed, ask model to continue without it
                    temp_history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    temp_history.append({
                        "role": "user",
                        "content": f"Tool failed: {result}. Please answer based on your knowledge."
                    })
                    continue
            
            # Check if model requested a web search
            search_pattern = r'SEARCH\s*\(\s*["\'](.+?)["\']\s*\)'
            search_matches = re.findall(search_pattern, response_text, re.IGNORECASE)
            
            if search_matches and WEB_SEARCH_AVAILABLE and search_count < max_search_attempts:
                search_count += 1
                query = search_matches[0]
                
                # Perform search
                search_results = web_search(query)
                
                if search_results is None:
                    # Search failed, ask model to answer without search
                    temp_history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    temp_history.append({
                        "role": "user",
                        "content": f"The search failed. Please answer based on your existing knowledge instead."
                    })
                    continue
                
                # Add assistant's search request to temp history
                temp_history.append({
                    "role": "assistant",
                    "content": response_text
                })
                
                # Add search results with clear instruction for final answer
                temp_history.append({
                    "role": "user",
                    "content": f"""[SEARCH RESULTS for "{query}"]

{search_results}

IMPORTANT: Based on these search results, provide your FINAL answer to the user's question.
Extract the key information (temperature, facts, data, etc.) and present it naturally.
Do NOT just list websites or sources - give the actual answer.
Do NOT request another search. Answer conversationally."""
                })
                
                # Continue loop to get final answer
                continue
            else:
                # No search needed or max searches reached - this is the final answer
                # Only save the original user message and final response to history
                history.append({"role": "assistant", "content": response_text})
                save_history(history)
                
                return response_text
        
        # If we exit loop without returning (too many searches)
        final_msg = "I apologize, but I'm having trouble finding the right information. Could you rephrase your question?"
        history.append({"role": "assistant", "content": final_msg})
        save_history(history)
        return final_msg
        
    except Exception as e:
        error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again."
        print(f"❌ Error in askAI: {e}")
        # Save error to history to maintain context
        history.append({"role": "assistant", "content": error_msg})
        save_history(history)
        return error_msg

# ------------------ Memory Logging ------------------
def log_interaction(input_text, response):
    """Log interaction to memory file"""
    try:
        memory = []
        if LOG_FILE.exists():
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                memory = json.load(f)
        
        memory.append({
            "time": datetime.utcnow().isoformat(),
            "input": input_text,
            "response": response[:500] + "..." if len(response) > 500 else response,
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
        "auto_search": WEB_SEARCH_AVAILABLE,
        "system_tools": True,
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
            
            response = askAI(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
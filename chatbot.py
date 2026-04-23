#------------------import -----------------------
from groq import Groq
from dotenv import load_dotenv
import os
import json
import math
from datetime import datetime

#------------------load env variables-----------------------
load_dotenv()

#------------------CONSTANTS-----------------------
MEMORY_FILE = "memory.json"
KNOWLEDGE_FILE = "knowledge.txt"
MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = "you are a helpful supprtive assistant for techlearn. Who help customers with the infromation,pricing,refunds and general queries use tools when you need real-time data like date/time, calculations, or web search. Use the provided context to answer the questions about the tech learn, and if you don't know anything, say no honestly"


#------------------initialize groq client-----------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


#------------------SECTION 1 : TOOLS-----------------------
def calculate(expression):
    """A simple calculator tool that evaluates basic math expressions."""
    try:
        result = eval(expression, 
        {"__builtins__": None},{"math": math, "sqrt": math.sqrt}
        )
        return f"{expression} = {result}"
    except Exception as e:
        return f"Could not calculate expression: {expression}: {e}"
    
    
    
def get_datetime():
    """A tool to get the current date and time."""
    now = datetime.now()
    return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"


def web_search(query):
    """A placeholder for a web search tool. In real implementations, we will call an api here"""
    
    query_lower = query.Lower()
     if "techlearn" in query_lower:
        return "Search results: TechLearn India is rated 4.5/5 on Google. Students praise the quality of content and affordable pricing. Most reviewed courses are ML and Data Science."

    elif "online course" in query_lower or "e-learning" in query_lower:
        return "Search results: Online learning in India grew 50% in 2024. Platforms like TechLearn, Udemy and Coursera are most popular. Students prefer courses with certificates and lifetime access."

    elif "machine learning" in query_lower:
        return "Search results: Machine Learning is the most in-demand skill in India in 2025. Average salary for ML engineers is 12-25 LPA. Python is the most used language."

    else:
        return f"Search results for '{query}': No strong results found. Please try a more specific query."

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a math expression. Use this for any calculation like discounts, totals, percentages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression to evaluate e.g. '4999 * 0.15' or '3999 + 4999'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Get the current date and time. Use when user asks about today's date, time, or day.",
            "parameters": {
                "type": "object",
                "properties": {}  # no arguments needed
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Use when user asks about reviews, trends, or external information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query e.g. 'TechLearn India reviews'"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# Maps string name → actual function
# LLM returns "calculate" as string → we look it up here → call the real function
available_functions = {
    "calculate": calculate,
    "get_datetime": get_datetime,
    "web_search": web_search
}


#-------------------SECTION 2: RAG (Read and Search knowledge)-----------------------
def load_knowledge():
    """ reads knowldege.txt file and splits into the chunks.
        one paragraph = one chunk
    """
    if not (os.path.exists(KNOWLEDGE_FILE)):
        print( f"Knowledge file '{KNOWLEDGE_FILE}' not found. RAG disabled.")
        return []
    
    with open(KNOWLEDGE_FILE, "r") as f:
        content = f.read()
        chunks = []
        for paragraph in content.split("\n\n"):
            chunks.append(paragraph.strip())
    return chunks

def retrieve(question, chunks , top_k = 2):
    """finds the most relevant chunks for the question, 
    uses the simple keyword matching - word overlap scoring"""
    if not chunks:
        return []
    
    question_words = question.lower().split()
    scores = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = 0
        for word in question_words:
            if word in chunk_lower:
                score += 1
                scores.append((score, chunk))
                
    scores.sort(key=lambda x: x[0], reverse=True) # sort by score in descending order
    return [chunk for score, chunk in scores[:top_k] if score > 0] # return top k chunks with score > 0


def build_rag_context(question, chunks):
    #retrieve relevant chunks
    relevant_chunks = retrieve(question, chunks)
    
    if not relevant_chunks:
        return "" #if no relevant chunks found
    
    context = "\n\n".join(relevant_chunks)
    return context


#-------------------SECTION 3: MEMORY (save and load memory)----------------------
def load_memory():
    #if there is any history in the memory file, then load the history, otherwise start with the system prompt
    if(os.path.exists(MEMORY_FILE)):
        with open(MEMORY_FILE, "r") as f:
            history = json.load(f)
            
         # Safety check — if file was corrupted and returned None
        if not history or not isinstance(history, list):
            print("Memory file corrupted. Starting fresh.\n")
            return [{"role": "system", "content": SYSTEM_PROMPT}]

        print(f"Loaded {len(history) - 1} past messages from memory.\n")
        return history
    else:
        print("No memory file found, starting fresh")
        return [{"role": "system", "content": SYSTEM_PROMPT}] #if no history found, then start with the system prompt and system role
    

def save_memory(history):
    #save the history to the memory file, after every conversation,
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)



#-----------------------SECTION 4: CHATBOT LOGIC (main function to handle user queries)-----------------------
def chat (history, user_input, chunks):
    '''
    1.RAG finds the relevant context from the knowledge file
    2. we will append the ralavant data with the user_input
    3. send to LLM and get the response
    4. if LLM calls a tool, we will execute the tool and get the result
    5. get final answer and update the history
    '''
    #1. Finding the relevant context using RAG
    context = build_rag_context(user_input, chunks)
    
    if context:
        full_message = f"""Use the following conpany information to answer the question:
        context: {context}
        customer question: {user_input}
        """
    else:
        full_message = user_input
        
    history.append({"role": "user", "content": full_message})
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=history,
        tools=tools,
        max_tokens=512,
        temperature=0.3,
        tool_choice = "auto",
    )
    response_message = response.choices[0].message
    
    #------------------tool handling logic will go here in future----------------------

            
    
    
    reply = response_message.content
    
    history.append({"role": "assistant", "content": reply})
    
    save_memory(history)
    
    return history,reply




#-----------------------SECTION 5: MAIN----------------------------------------------
def main():
    print("=" * 50)
    print(" Techlearn India - AI customer support chatbot")
    print("=" * 50)
    print("I can help you with:")
    print("  • Course info, pricing, refunds, enrollment")
    print("  • Calculations  (e.g. discounts, totals)")
    print("  • Current date and time")
    print("  • Web search for reviews and trends")
    print("\nCommands: 'quit' | 'clear' | 'history'")
    print("=" * 55 + "\n")
    
    chunks = load_knowledge()
    print(f"Loaded {len(chunks)} knowledge chunks.\n")
    history = load_memory()
    
    while True:
        user_input = input("you:").strip()
        if not user_input:
            continue
        
        if user_input.lower() == "quit":
            print("goodbye!")
            break
        
        if user_input.lower() == "clear":
            if os.path.exists(MEMORY_FILE):
                os.remove(MEMORY_FILE)
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("Memory cleared. Starting fresh.")
            continue
        
        if user_input.lower() == "history":
            print("\n--- Conversation History ---")
           for msg in history:
                if msg["role"] == "system":
                    continue
                if isinstance(msg, dict) and "role" in msg:
                    role = "You" if msg["role"] == "user" else "Bot"
                    content = msg.get("content", "")
                    if content:
                        print(f"{role}: {str(content)[:80]}")
            print("--- End of History ---\n")
            continue
        
        history, reply = chat(history, user_input, chunks)
        print(f"assistant: {reply}\n")


if __name__ == "__main__":
    main()
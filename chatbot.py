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
    
    


#-------------------SECTION 3: MEMORY (save and load memory)----------------------
def load_memory():
    #if there is any history in the memory file, then load the history, otherwise start with the system prompt
    if(os.path.exists(MEMORY_FILE)):
        with open(MEMORY_FILE, "r") as f:
            history = json.load(f)
    else:
        print("No memory file found, starting fresh")
        return [{"role": "system", "content": SYSTEM_PROMPT}] #if no history found, then start with the system prompt and system role
    

def save_memory(history):
    #save the history to the memory file, after every conversation,
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)



#-----------------------SECTION 4: CHATBOT LOGIC (main function to handle user queries)-----------------------




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


if __name__ == "__main__":
    main()
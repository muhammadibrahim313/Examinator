from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.state import CompiledStateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from typing import Annotated, TypedDict, List, Optional
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import WikipediaLoader
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
import os,re
import operator
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import random
import time

load_dotenv()

# HYBRID MODEL SYSTEM: Groq (primary) + Google Gemini (fallback)
class HybridModelManager:
    """Manages both Groq and Google Gemini models with intelligent failover"""
    
    def __init__(self):
        self.groq_calls = 0
        self.gemini_calls = 0
        self.groq_failures = 0
        self.gemini_failures = 0
        self.last_groq_failure = 0
        self.last_gemini_failure = 0
        self.groq_cooldown = 60  # seconds
        self.gemini_cooldown = 300  # 5 minutes for quota issues
        
    def get_primary_model(self):
        """Get Groq model (primary) - faster and higher limits"""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        return ChatGroq(
            model="llama3-8b-8192",  # Updated to current production model
            api_key=groq_api_key,
            temperature=0.3,
            max_tokens=4096,
            timeout=30
        )
    
    def get_fallback_model(self):
        """Get Google Gemini model (fallback) - reliable backup"""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            api_key=google_api_key,
            temperature=0.3
        )
    
    def should_use_groq(self):
        """Determine if Groq should be used (not in cooldown)"""
        current_time = time.time()
        groq_ready = (current_time - self.last_groq_failure) > self.groq_cooldown
        groq_available = os.getenv("GROQ_API_KEY") is not None
        return groq_available and groq_ready
    
    def should_use_gemini(self):
        """Determine if Gemini should be used (not in cooldown)"""
        current_time = time.time()
        gemini_ready = (current_time - self.last_gemini_failure) > self.gemini_cooldown
        gemini_available = os.getenv("GOOGLE_API_KEY") is not None
        return gemini_available and gemini_ready
    
    async def get_model_response(self, messages, use_async=True):
        """Get response from models with intelligent failover"""
        current_time = time.time()
        
        # Strategy 1: Try Groq first (faster, higher limits)
        if self.should_use_groq():
            try:
                print("🚀 Using Groq (primary)")
                model = self.get_primary_model()
                
                if use_async:
                    response = await model.ainvoke(messages)
                else:
                    response = model.invoke(messages)
                
                self.groq_calls += 1
                print(f"✅ Groq success (calls: {self.groq_calls})")
                return response, "groq"
                
            except Exception as e:
                self.groq_failures += 1
                self.last_groq_failure = current_time
                print(f"❌ Groq failed: {str(e)[:100]}...")
                print(f"🔄 Falling back to Gemini")
        
        # Strategy 2: Try Gemini as fallback
        if self.should_use_gemini():
            try:
                print("🔧 Using Gemini (fallback)")
                model = self.get_fallback_model()
                
                if use_async:
                    response = await model.ainvoke(messages)
                else:
                    response = model.invoke(messages)
                
                self.gemini_calls += 1
                print(f"✅ Gemini success (calls: {self.gemini_calls})")
                return response, "gemini"
                
            except Exception as e:
                self.gemini_failures += 1
                self.last_gemini_failure = current_time
                print(f"❌ Gemini failed: {str(e)[:100]}...")
                raise Exception(f"Both models failed - Groq: {str(e)[:50]}")
        
        # Strategy 3: If both are in cooldown, try anyway (emergency)
        print("⚠️ Both models in cooldown, trying emergency fallback")
        try:
            model = self.get_fallback_model()
            if use_async:
                response = await model.ainvoke(messages)
            else:
                response = model.invoke(messages)
            return response, "gemini-emergency"
        except Exception as e:
            raise Exception(f"All models failed: {str(e)}")
    
    def get_model_response_sync(self, messages):
        """Synchronous version of get_model_response"""
        current_time = time.time()
        
        # Strategy 1: Try Groq first (faster, higher limits)
        if self.should_use_groq():
            try:
                print("🚀 Using Groq (primary)")
                model = self.get_primary_model()
                response = model.invoke(messages)
                
                self.groq_calls += 1
                print(f"✅ Groq success (calls: {self.groq_calls})")
                return response, "groq"
                
            except Exception as e:
                self.groq_failures += 1
                self.last_groq_failure = current_time
                print(f"❌ Groq failed: {str(e)[:100]}...")
                print(f"🔄 Falling back to Gemini")
        
        # Strategy 2: Try Gemini as fallback
        if self.should_use_gemini():
            try:
                print("🔧 Using Gemini (fallback)")
                model = self.get_fallback_model()
                response = model.invoke(messages)
                
                self.gemini_calls += 1
                print(f"✅ Gemini success (calls: {self.gemini_calls})")
                return response, "gemini"
                
            except Exception as e:
                self.gemini_failures += 1
                self.last_gemini_failure = current_time
                print(f"❌ Gemini failed: {str(e)[:100]}...")
                raise Exception(f"Both models failed - Gemini: {str(e)[:50]}")
        
        # Strategy 3: If both are in cooldown, try anyway (emergency)
        print("⚠️ Both models in cooldown, trying emergency fallback")
        try:
            model = self.get_fallback_model()
            response = model.invoke(messages)
            return response, "gemini-emergency"
        except Exception as e:
            raise Exception(f"All models failed: {str(e)}")
    
    def get_stats(self):
        """Get usage statistics"""
        total_calls = self.groq_calls + self.gemini_calls
        return {
            "total_calls": total_calls,
            "groq_calls": self.groq_calls,
            "gemini_calls": self.gemini_calls,
            "groq_failures": self.groq_failures,
            "gemini_failures": self.gemini_failures,
            "groq_success_rate": (self.groq_calls / max(1, self.groq_calls + self.groq_failures)) * 100,
            "gemini_success_rate": (self.gemini_calls / max(1, self.gemini_calls + self.gemini_failures)) * 100
        }

# Global hybrid model manager
hybrid_manager = HybridModelManager()

class QuestionState(MessagesState):
    query: str
    context: Annotated[List[str], operator.add]
    question: str
    wiki_complete: bool
    web_complete: bool
    query_safe: bool
    summarized_content: Annotated[list[str], operator.add]

# OPTIMIZATION: Simplified query check - skip expensive LLM moderation for educational content
def check_query(state: QuestionState):
    """Simplified query validation without LLM calls"""
    try:
        query = state['query'].lower()
        
        # Simple rule-based filtering for obvious inappropriate content
        inappropriate_keywords = [
            'porn', 'sex', 'nude', 'xxx', 'adult', 'explicit', 
            'nsfw', 'erotic', 'sexual', 'dick', 'pussy', 'fuck'
        ]
        
        is_safe = not any(keyword in query for keyword in inappropriate_keywords)
        
        print(f"🔍 Query Safety Check: {'✅ SAFE' if is_safe else '❌ UNSAFE'}")
        
        if not is_safe:
            return {
                "query": state['query'],
                "context": ["Query flagged as inappropriate and cannot be processed."],
                "question": state['query'],
                "query_safe": False,
                "wiki_complete": True,
                "web_complete": True,
                "summarized_content": ["Query flagged as inappropriate and cannot be processed."]
            }
        
        return {
            "query": state['query'],
            "context": [],
            "question": state['query'],
            "query_safe": True,
            "wiki_complete": False,
            "web_complete": False
        }
        
    except Exception as e:
        print(f"⚠️ Error checking query: {str(e)}")
        return {
            "query": state['query'],
            "context": [f"Error in query safety check: {str(e)}"],
            "question": state['query'],
            "query_safe": True,  # Default to safe for educational content
            "wiki_complete": False,
            "web_complete": False,
            "summarized_content": []
        }

def wiki_search(state: QuestionState):
    """Search Wikipedia and return details"""
    try:
        print(f"📚 Starting Wikipedia search for: {state['query']}")
        
        docs = WikipediaLoader(query=state['query'], load_max_docs=2).load()  # Reduced from 3 to 2
        
        if not docs:
            print("❌ No Wikipedia documents found")
            return {
                'context': ["No Wikipedia results found for the query."],
                'wiki_complete': True
            }
        
        formatted_docs = []
        
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown Source")
            title = doc.metadata.get("title", "Unknown Title")
            content_preview = doc.page_content[:300]
            
            print(f"📄 Wikipedia Result {i+1}: {title}")
            print(f"🔗 Source: {source}")
            print(f"📝 Preview: {content_preview}...\n")
            
            # Reduced content length to save on processing
            formatted_docs.append(
                f'<WikipediaDocument title="{title}" source="{source}">\n'
                f'{doc.page_content[:800]}...\n'  # Reduced from 1000 to 800
                f'</WikipediaDocument>'
            )
        
        return {
            'context': formatted_docs,
            'wiki_complete': True
        }
        
    except Exception as e:
        print(f"⚠️ Wikipedia Search Error: {str(e)}")
        return {
            'context': [f"Wikipedia search error: {str(e)}"],
            'wiki_complete': True
        }

def web_search(state: QuestionState):
    """Search the web using Tavily"""
    try:
        print(f"🌐 Starting web search for: {state['query']}")
        
        tool = TavilySearchResults(max_results=2)  # Reduced from 3 to 2
        search_results = tool.invoke(state['question'])
        
        if not search_results:
            print("❌ No web search results found")
            return {
                'context': ["No web search results found for the query."],
                'web_complete': True
            }
        
        formatted_docs = []
        
        for i, result in enumerate(search_results):
            url = result.get("url", "No URL")
            title = result.get("title", "No Title")
            content = result.get("content", "No content")
            content_preview = content[:300] if content else "No preview available"
            
            print(f"🌍 Web Result {i+1}: {title}")
            print(f"🔗 URL: {url}")
            print(f"📝 Preview: {content_preview}...\n")
            
            # Reduced content length
            formatted_docs.append(
                f'<WebDocument title="{title}" url="{url}">\n'
                f'{content[:800] if content else "No content"}...\n'  # Reduced from 1000 to 800
                f'</WebDocument>'
            )
        
        return {
            'context': formatted_docs,
            'web_complete': True
        }
        
    except Exception as e:
        print(f"⚠️ Web Search Error: {str(e)}")
        return {
            'context': [f"Web search error: {str(e)}"],
            'web_complete': True
        }

def should_continue_to_summary(state: QuestionState):
    """Determine if both searches are complete and query is safe"""
    if not state.get('query_safe', False):
        return "end"
    
    wiki_done = state.get('wiki_complete', False)
    web_done = state.get('web_complete', False)
    
    if wiki_done and web_done:
        return "summarize"
    else:
        return "continue"

# OPTIMIZATION: Hybrid model summarization
def summarize_content(state: QuestionState):
    """Summarize the collected content using hybrid model system"""
    try:
        print("📊 Starting hybrid model summarization...")
        
        # Combine all context
        all_context = "\n\n".join(state.get('context', []))
        
        # Simplified system message to reduce token usage
        sys_msg = f"""Based on the search results for "{state['query']}", provide a concise, helpful summary. 
        Include key facts and information. Be direct and informative.
        
        Search Results:
        {all_context[:2000]}"""  # Limit context length to reduce tokens

        messages = [
            SystemMessage(content=sys_msg),
            HumanMessage(content=f"Summarize: {state['query']}")
        ]

        # Use hybrid model manager synchronously
        response, model_used = hybrid_manager.get_model_response_sync(messages)
        
        print(f"✅ Summary generated successfully using {model_used}")
        
        summary_text = response.content
        
        return {
            "context": [summary_text],  # Simplified - just the summary
            "summarized_content": [summary_text]
        }
        
    except Exception as e:
        print(f"⚠️ Error in summarization: {str(e)}")
        error_msg = f"Error generating summary: {str(e)}"
        return {
            "context": [error_msg],
            "summarized_content": [error_msg]
        }

# OPTIMIZATION: Simplified graph structure
builder = StateGraph(QuestionState)

builder.add_node("check_query", check_query)
builder.add_node("wiki_search", wiki_search)
builder.add_node("web_search", web_search)
builder.add_node("summarize_content", summarize_content)

builder.add_edge(START, "check_query")
builder.add_edge("check_query", "wiki_search")
builder.add_edge("check_query", "web_search")
builder.add_edge("wiki_search", "summarize_content")
builder.add_edge("web_search", "summarize_content")
builder.add_edge("summarize_content", END)

Parallel_Search: CompiledStateGraph = builder.compile()

###########################################################################################################
# MAIN GRAPH - HYBRID MODEL VERSION

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from dotenv import load_dotenv
from typing import Union

load_dotenv()

current_date = datetime.now().strftime("%A, %B %d, %Y")

# OPTIMIZATION: Reduced max retries to save API calls
MAX_SEARCH_RETRIES = 2  # Reduced from 5 to 2

class GraphState(MessagesState):
    original_question: str
    attempted_search_queries: list[str]
    summarized_content: Annotated[list[str], operator.add]

@tool
def web_search_tool(query: str) -> str:
    """Search the web for current information using parallel Wikipedia and web search. 
    Use this tool to find up-to-date information about any topic."""
    return f"web_search_tool_called_with_query:{query}"

# OPTIMIZATION: Use hybrid model initialization
def get_model_with_tools():
    """Get model with tools bound - hybrid system"""
    # Try Groq first if available, then Gemini
    try:
        if hybrid_manager.should_use_groq():
            model = hybrid_manager.get_primary_model()
            print("🚀 Using Groq for tool binding")
            return model.bind_tools([web_search_tool])
    except Exception as e:
        print(f"⚠️ Groq tool binding failed: {e}")
    
    # Fallback to Gemini
    try:
        model = hybrid_manager.get_fallback_model()
        print("🔧 Using Gemini for tool binding")
        return model.bind_tools([web_search_tool])
    except Exception as e:
        print(f"❌ Both model tool binding failed: {e}")
        raise e

# OPTIMIZATION: Removed expensive relevance filter
async def should_continue(state: GraphState):
    if len(state["attempted_search_queries"]) >= MAX_SEARCH_RETRIES:
        return END
    
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "web_search"
    return END  # Skip reflection to save API calls

# OPTIMIZATION: Hybrid model call
async def call_model(state: GraphState):
    system_message = SystemMessage(content=f"""
    You are a helpful research assistant. Answer questions comprehensively using web search when needed.
    Current date: {current_date}
    
    Use the web_search_tool for questions requiring current information or specific facts.
    Be direct and helpful in your responses.
    """)
    
    conversation_messages = [system_message] + state["messages"]
    
    try:
        # Get model with tools using hybrid system
        model_with_tools = get_model_with_tools()
        response = await model_with_tools.ainvoke(conversation_messages)
        
        print("$"*50)
        print("response tool_calls:", getattr(response, 'tool_calls', []))
        print("response content:", response.content[:200] + "..." if len(response.content) > 200 else response.content)
        
        if hasattr(response, 'tool_calls') and response.tool_calls:
            search_query = response.tool_calls[0]['args']['query']
            return {
                "messages": [response],
                "attempted_search_queries": state["attempted_search_queries"] + [search_query],
            }
        return {"messages": [response]}
        
    except Exception as e:
        print(f"❌ Hybrid model call failed: {e}")
        # Return error message instead of crashing
        error_response = HumanMessage(content=f"I encountered a technical issue: {str(e)[:100]}. Please try again.")
        return {"messages": [error_response]}

async def web_search(state: GraphState):
    last_message = state["messages"][-1]
    
    if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
        raise Exception("web_search called without tool calls in last message")
    
    tool_call = last_message.tool_calls[0]
    
    subgraph_input = {
        "query": tool_call['args']['query'],
        "question": tool_call['args']['query'],
        "context": [],
        "wiki_complete": False,
        "web_complete": False,
        "query_safe": True,
        "messages": [],
        "summarized_content": []
    }
    
    try:
        search_results = await Parallel_Search.ainvoke(subgraph_input)
        
        context_results = search_results.get('context', [])
        summarized_results = search_results.get('summarized_content', [])
        
        print("🔍 Subgraph Results:")
        print(f"Context results: {len(context_results)} items")
        print(f"Summarized results: {len(summarized_results)} items")
        
        if not context_results:
            context_results = ["No search results found."]
        if not summarized_results:
            summarized_results = ["No summarized content available."]
        
        # Simplified tool message
        tool_message = ToolMessage(
            content=json.dumps({"results": context_results}),
            tool_call_id=tool_call['id'],
            name="web_search_tool"
        )
        
        return {
            "messages": [tool_message],
            "summarized_content": summarized_results
        }
        
    except Exception as e:
        print(f"Error in subgraph execution: {e}")
        error_message = f"Search error: {str(e)}"
        tool_message = ToolMessage(
            content=json.dumps({"results": [error_message]}),
            tool_call_id=tool_call['id'],
            name="web_search_tool"
        )
        return {
            "messages": [tool_message],
            "summarized_content": [error_message]
        }

# OPTIMIZATION: Simplified workflow without expensive evaluations
workflow = StateGraph(GraphState, input=MessagesState, output=MessagesState)

workflow.add_node(
    "store_original_question",
    lambda state: {
        "original_question": state["messages"][-1].content,
        "attempted_search_queries": [],
    },
)
workflow.add_node("agent", call_model)
workflow.add_node("web_search", web_search)

workflow.add_edge(START, "store_original_question")
workflow.add_edge("store_original_question", "agent")
workflow.add_conditional_edges("agent", should_continue, ["web_search", END])
workflow.add_edge("web_search", "agent")

agent = workflow.compile()

# OPTIMIZATION: Simplified main function with stats
async def run_main():
    """Main function for testing - only runs when called explicitly"""
    config = {"recursion_limit": 20}  # Reduced from 50 to 20
    user_query = input("Enter your question: ")
    
    print("\n🚀 Starting hybrid model system...")
    stats_before = hybrid_manager.get_stats()
    print(f"📊 Initial stats: {stats_before}")
    
    async for chunk in agent.astream(
        {"messages": [HumanMessage(content=user_query)]},
        config=config
    ):
        print(chunk)
        print("-"*40)
    
    stats_after = hybrid_manager.get_stats()
    print(f"\n📊 Final stats: {stats_after}")
    print(f"🎯 Calls this session: Groq={stats_after['groq_calls']-stats_before['groq_calls']}, Gemini={stats_after['gemini_calls']-stats_before['gemini_calls']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_main())
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.state import CompiledStateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
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

load_dotenv()

from openevals.llm import create_async_llm_as_judge
from openevals.prompts import (
    RAG_RETRIEVAL_RELEVANCE_PROMPT,
    RAG_HELPFULNESS_PROMPT,
)

model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

class QuestionState(MessagesState):
    query: str
    context: Annotated[List[str], operator.add]
    question: str
    wiki_complete: bool
    web_complete: bool
    query_safe: bool
    summarized_content: Annotated[list[str], operator.add]  # Store summarized content



def check_query(state: QuestionState):
    """Check if the query is valid and safe"""
    try:
        sys_msg = """
        You are a strict content moderation agent. Your task is to examine user queries and determine if they contain any inappropriate, explicit, or adult (18+) content, including but not limited to:

        - Sexual or pornographic content
        - Nudity or erotic material
        - Offensive or vulgar language
        - Violence, abuse, or harassment with sexual context
        - Sexually suggestive or exploitative content

        If the query contains any such content, respond with:
        "UNSAFE: This query contains inappropriate content."

        If the query is safe, respond with:
        "SAFE: Query is appropriate to proceed."

        Be strict and cautious. When in doubt, flag the query.
        """

        messages = [
            SystemMessage(content=sys_msg),
            HumanMessage(content=state['query'])
        ]

        response = model.invoke(messages)
        content = response.content.lower()
        
        # Check if query is safe
        is_safe = "safe:" in content and "unsafe:" not in content
        
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
            "context": [f"Query safety check: {response.content}"],
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
            "query_safe": False,
            "wiki_complete": True,
            "web_complete": True,
            "summarized_content": [f"Error in query safety check: {str(e)}"]
        }



def wiki_search(state: QuestionState):
    """Search Wikipedia and return details"""
    try:
        print(f"📚 Starting Wikipedia search for: {state['query']}")
        
        docs = WikipediaLoader(query=state['query'], load_max_docs=3).load()
        
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
            
            formatted_docs.append(
                f'<WikipediaDocument title="{title}" source="{source}">\n'
                f'{doc.page_content[:1000]}...\n'
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
        
        tool = TavilySearchResults(max_results=3)
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
            
            formatted_docs.append(
                f'<WebDocument title="{title}" url="{url}">\n'
                f'{content[:1000] if content else "No content"}...\n'
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


def summarize_content(state: QuestionState):
    """Summarize the collected content and store in summarized_content"""
    try:
        print("📊 Starting content summarization...")
        
        # Combine all context
        all_context = "\n\n".join(state.get('context', []))
        
        sys_msg = f"""
        You are a helpful research assistant. Based on the following search results about the user's query: "{state['query']}", 
        please provide a comprehensive summary that addresses their question.

        Search Results:
        {all_context}

        Instructions:
        1. Provide a clear, well-structured summary
        2. Include specific information and details found in the sources
        3. Organize the information logically
        4. If information is limited, acknowledge this
        5. Focus on actionable insights for the user

        Please provide your summary:
        """

        messages = [
            SystemMessage(content=sys_msg),
            HumanMessage(content=f"Please summarize the search results for: {state['query']}")
        ]

        response = model.invoke(messages)
        
        print("✅ Summary generated successfully")
        print(response.content)
        
        summary_text = response.content
        formatted_summary = f"\n{'='*50}\nFINAL SUMMARY:\n{'='*50}\n{summary_text}"
        
        return {
            "context": [formatted_summary],
            "summarized_content": [summary_text]  # Store clean summary for relevance filter
        }
        
    except Exception as e:
        print(f"⚠️ Error in summarization: {str(e)}")
        error_msg = f"Error generating summary: {str(e)}"
        return {
            "context": [error_msg],
            "summarized_content": [error_msg]
        }

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

# End after summarization
builder.add_edge("summarize_content", END)

Parallel_Search: CompiledStateGraph = builder.compile()





###########################################################################################################
# MAIN GRAPH 

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from dotenv import load_dotenv
from typing import Union

load_dotenv()

current_date = datetime.now().strftime("%A, %B %d, %Y")


MAX_SEARCH_RETRIES = 5



relevance_evaluator = create_async_llm_as_judge(
    judge=model,
    prompt=RAG_RETRIEVAL_RELEVANCE_PROMPT + f"\n\nThe current date is {current_date}.",
    feedback_key="retrieval_relevance",
)

helpfulness_evaluator = create_async_llm_as_judge(
    judge=model,
    prompt=RAG_HELPFULNESS_PROMPT
    + f'\nReturn "true" if the answer is helpful, and "false" otherwise.\n\nThe current date is {current_date}.',
    feedback_key="helpfulness",
)



class GraphState(MessagesState):
    original_question: str
    attempted_search_queries: list[str]
    summarized_content: Annotated[list[str], operator.add]  # pulled from summarize step



@tool
def web_search_tool(query: str) -> str:
    """Search the web for current information using parallel Wikipedia and web search. 
    Use this tool to find up-to-date information about any topic."""
    return f"web_search_tool_called_with_query:{query}"

# Bind the tool to the model
model_with_tools = model.bind_tools([web_search_tool])




async def relevance_filter(state: GraphState):

    last_message = state["messages"][-1]

    summarized_context = state['summarized_content']
    # FIXED: Ensure we're processing a tool message
    if not (last_message.type == "tool" and last_message.name == "web_search_tool"):
        raise Exception(f"Relevance filter node must be called after web search, got message type: {last_message.type}")
    
    search_results_content = summarized_context


    try:
        if isinstance(search_results_content, str):
            search_data = json.loads(search_results_content)
        else:
            search_data = search_results_content
    except json.JSONDecodeError:
        search_data = {"results": [{"content": search_results_content}]}
    
    search_results = search_data
    
    filtered_results = []
    
    semaphore = asyncio.Semaphore(2)

    async def evaluate_with_semaphore(result):
        async with semaphore:
            try:
                eval_result = await relevance_evaluator(
                    inputs=state["attempted_search_queries"][-1], 
                    context=result
                )
                return result, eval_result
            except Exception as e:
                print(f"Evaluation error: {e}")
                return result, {"score": True} 

    tasks = [evaluate_with_semaphore(result) for result in search_results]
    
    for completed_task in asyncio.as_completed(tasks):
        result, eval_result = await completed_task
        if eval_result.get("score", False):
            filtered_results.append(result)

    # Create filtered message
    filtered_message = ToolMessage(
        content=json.dumps({"results": filtered_results}),
        tool_call_id=last_message.tool_call_id,
        name=last_message.name
    )
    
    return {"messages": [filtered_message]}




async def should_continue(state: GraphState):
    if len(state["attempted_search_queries"]) >= MAX_SEARCH_RETRIES:
        return END
    
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "web_search"
    return "reflect"



async def call_model(state: GraphState):
    system_message = SystemMessage(content=f"""
    You are a helpful research assistant with access to web search capabilities. Your task is to answer user questions comprehensively.
    
    Current date: {current_date}
    
    IMPORTANT: You have access to a web_search_tool that can search the internet for current information. Use this tool when:
    1. You need current or recent information
    2. The user asks about specific facts, research, or data
    3. You want to provide a comprehensive answer with up-to-date information
    4. The question requires information beyond your training data
    
    Instructions:
    - ALWAYS use the web_search_tool for questions that would benefit from current information
    - Provide comprehensive answers based on search results
    - Be helpful and informative
    
    Remember: You CAN and SHOULD use the web_search_tool to get current information!
    """)
    
    conversation_messages = [system_message] + state["messages"]
    
    response = await model_with_tools.ainvoke(conversation_messages)
    
    print("$"*50)
    print("response tool_calls:", response.tool_calls)
    print("response content:", response.content[:200] + "..." if len(response.content) > 200 else response.content)
    
    # Handle tool calls properly
    if hasattr(response, 'tool_calls') and response.tool_calls:
        search_query = response.tool_calls[0]['args']['query']
        return {
            "messages": [response],
            "attempted_search_queries": state["attempted_search_queries"] + [search_query],
        }
    return {"messages": [response]}




async def web_search(state: GraphState):
    last_message = state["messages"][-1]
    
    if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
        raise Exception("web_search called without tool calls in last message")
    
    tool_call = last_message.tool_calls[0]
    
    # FIXED: Properly invoke the subgraph
    subgraph_input = {
        "query": tool_call['args']['query'],
        "question": tool_call['args']['query'],
        "context": [],
        "wiki_complete": False,
        "web_complete": False,
        "query_safe": True,
        "messages": [],  # Required by MessagesState
        "summarized_content": []  # Initialize the new field
    }
    
    try:
        search_results = await Parallel_Search.ainvoke(subgraph_input)
        
        # Extract the context and summarized content from the subgraph results
        context_results = search_results.get('context', [])
        summarized_results = search_results.get('summarized_content', [])
        
        print("🔍 Subgraph Results:")
        print(f"Context results: {len(context_results)} items")
        print(f"Summarized results: {len(summarized_results)} items")
        
        # FIXED: Ensure we have proper results format
        if not context_results:
            context_results = ["No search results found."]
        if not summarized_results:
            summarized_results = ["No summarized content available."]
        
        tool_message = ToolMessage(
            content=json.dumps({
                "results": [{"content": result} for result in context_results],
                "summarized_results": [{"content": summary} for summary in summarized_results]
            }),
            tool_call_id=tool_call['id'],
            name="web_search_tool"
        )
        
        return {
            "messages": [tool_message],
            "context": context_results,
            "summarized_content": summarized_results  # Pass the summarized content from subgraph
        }
        
    except Exception as e:
        print(f"Error in subgraph execution: {e}")
        error_message = f"Search error: {str(e)}"
        tool_message = ToolMessage(
            content=json.dumps({"results": [{"content": error_message}]}),
            tool_call_id=tool_call['id'],
            name="web_search_tool"
        )
        return {
            "messages": [tool_message],
            "context": [error_message],
            "summarized_content": [error_message]
        }



async def reflect(state: GraphState):
    last_message = state["messages"][-1]
    
    # Only evaluate non-tool messages
    if last_message.type == "tool":
        return {}
    
    try:
        helpfulness_eval_result = await helpfulness_evaluator(
            inputs=state["original_question"], 
            outputs=last_message.content
        )
        
        if not helpfulness_eval_result.get("score", False):
            reflection_message = HumanMessage(content=f"""
                    I originally asked you the following question:

                    <original_question>
                    {state["original_question"]}
                    </original_question>

                    Your answer was not helpful for the following reason:

                    <reason>
                    {helpfulness_eval_result.get('comment', 'The answer was not helpful.')}
                    </reason>

                    Please check the conversation history carefully and try again. You may choose to fetch more information if you think the answer
                    to the original question is not somewhere in the conversation, but carefully consider if the answer is already in the conversation.

                    You have already attempted to answer the original question using the following search queries,
                    so if you choose to search again, you must rephrase your search query to be different from the ones below to avoid fetching redundant information:

                    <attempted_search_queries>
                    {state['attempted_search_queries']}
                    </attempted_search_queries>

                    As a reminder, check the previous conversation history and fetched context carefully before searching again!
            """)
            return {"messages": [reflection_message]}
    except Exception as e:
        print(f"Error in reflection: {e}")
    
    return {}

async def retry_or_end(state: GraphState):
    if state["messages"][-1].type == "human":
        return "agent"
    return END



# FIXED: Main workflow definition
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
workflow.add_node("relevance_filter", relevance_filter)
workflow.add_node("reflect", reflect)

workflow.add_edge(START, "store_original_question")
workflow.add_edge("store_original_question", "agent")
workflow.add_conditional_edges("agent", should_continue, ["web_search", "reflect", END])
workflow.add_edge("web_search", "relevance_filter")
workflow.add_edge("relevance_filter", "agent")
workflow.add_conditional_edges("reflect", retry_or_end, ["agent", END])

agent = workflow.compile()


# FIXED: Remove the problematic await call outside function
async def run_main():
    """Main function for testing - only runs when called explicitly"""
    config = {"recursion_limit": 50}
    user_query = input("Enter your question: ")
    async for chunk in agent.astream(
        {"messages": [HumanMessage(content=user_query)]},
        config=config
    ):
        print(chunk)
        print("-"*40)

# Only run if this file is executed directly (not imported)
if __name__ == "__main__":
    import asyncio
    asyncio.run(run_main())
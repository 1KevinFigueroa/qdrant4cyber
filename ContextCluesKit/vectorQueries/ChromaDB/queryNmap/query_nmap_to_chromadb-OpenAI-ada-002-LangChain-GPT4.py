"""
Nmap ChromaDB LangChain Q&A
----------------------------
This script provides an interactive LangChain-powered Q&A interface to ask
open-ended questions about nmap scan results already stored in ChromaDB.

Usage:
    python query_nmap_to_chromadb-OpenAI-ada-002-LangChain-GPT4.py

Note:
    Data must be imported first using import_nmap_to_chromadb-OpenAI-ada-002.py
"""

import os
import sys
import chromadb
from dotenv import load_dotenv

# LangChain imports
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COLLECTION_NAME = "nmaptest_openAI"
CHROMADB_HOST = "localhost"
CHROMADB_PORT = 9000
CHROMADB_AUTH_TOKEN = "my-secret-token"


# ---------------------------------------------------------------------------
# LangChain Q&A
# ---------------------------------------------------------------------------

def build_qa_chain():
    """
    Build a LangChain retrieval chain backed by the ChromaDB collection
    that was populated during import, with conversation history support.

    Returns (chain, chat_history) ready to accept questions.
    """
    load_dotenv()

    api_key = os.getenv("OpenAI_API_KEY")
    if not api_key:
        print("❌ Error: OpenAI_API_KEY not found in environment / .env file.")
        return None, None

    # --- Embeddings (must match what was used during import) ----------------
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=api_key
    )

    # --- Connect LangChain to the existing ChromaDB collection --------------
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        client=chromadb.HttpClient(
            host=CHROMADB_HOST,
            port=CHROMADB_PORT,
            headers={"Authorization": f"Bearer {CHROMADB_AUTH_TOKEN}"}
        ),
    )

    # Quick sanity check
    doc_count = vectorstore._collection.count()
    if doc_count == 0:
        print("⚠️  The ChromaDB collection is empty. Import data first.")
        return None, None
    print(f"✓ Connected to ChromaDB collection '{COLLECTION_NAME}' ({doc_count} documents)")

    # --- Retriever ---------------------------------------------------------
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 20},  # return top-20 most relevant hosts
    )

    # --- LLM ---------------------------------------------------------------
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0,
        openai_api_key=api_key,
    )

    # --- History-aware retriever -------------------------------------------
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Given the chat history and the latest user question, "
         "reformulate the question into a standalone question that can be "
         "understood without the chat history. Do NOT answer the question — "
         "just reformulate it if needed, otherwise return it as-is."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # --- Answer chain (stuff documents into a prompt) ----------------------
    qa_system_prompt = (
        "You are a senior network security analyst assistant. You answer "
        "questions about nmap scan results that have been stored in a "
        "vector database.\n\n"
        "Use ONLY the following context (retrieved nmap host records) to "
        "answer. If the context does not contain enough information, say "
        "so — do not make up data.\n\n"
        "When answering:\n"
        "- Reference specific IP addresses, ports, services, and OS details.\n"
        "- Highlight potential security concerns (e.g. open admin ports, "
        "outdated software versions, unnecessary services).\n"
        "- Provide actionable recommendations when asked.\n"
        "- Format tables or lists when they improve clarity.\n\n"
        "{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # --- Full retrieval chain ----------------------------------------------
    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    chat_history = []

    return chain, chat_history


def interactive_chat(chain, chat_history):
    """Run an interactive Q&A session in the terminal."""
    print("\n" + "=" * 70)
    print("🔍 Nmap Scan Q&A  (powered by LangChain + OpenAI)")
    print("=" * 70)
    print("Ask anything about your scan results. Type 'exit' to quit.\n")

    print("Example questions:")
    print("  • Which hosts have port 22 (SSH) open?")
    print("  • Summarize the most critical security findings.")
    print("  • What operating systems were detected?")
    print("  • Are there any hosts running outdated software?")
    print("  • List all web servers found in the scan.")
    print()

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break
        if question.lower() == "clear":
            chat_history.clear()
            print("🗑  Conversation history cleared.\n")
            continue

        try:
            result = chain.invoke({
                "input": question,
                "chat_history": chat_history,
            })
            answer = result.get("answer", "No answer returned.")

            # Update chat history
            chat_history.append(HumanMessage(content=question))
            chat_history.append(AIMessage(content=answer))

            # Show the answer
            print(f"\nAssistant: {answer}\n")

            # Optionally show which hosts were used as context
            sources = result.get("context", [])
            if sources:
                unique_ips = set()
                for doc in sources:
                    ip = doc.metadata.get("ip_address")
                    if ip:
                        unique_ips.add(ip)
                if unique_ips:
                    print(f"  📎 Sources: {', '.join(sorted(unique_ips))}\n")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Main function."""
    chain, chat_history = build_qa_chain()
    if chain:
        interactive_chat(chain, chat_history)
    else:
        print("\n❌ Could not start Q&A. Make sure data has been imported first.")
        sys.exit(1)


if __name__ == "__main__":
    main()

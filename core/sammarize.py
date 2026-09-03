import os

from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# 🤖 LLM
# ============================================================

# def get_llm():

#     return ChatMistralAI(
#         model="mistral-small-latest",
#         mistral_api_key=os.getenv("MISTRAL_API_KEY"),
#         temperature=0.3
#     )

def get_llm():
  return ChatGroq(model="openai/gpt-oss-120b",groq_api_key= os.getenv("GROQ_API_KEY"),temperature=0.2)

# ============================================================
# ✂️ Split Transcript
# ============================================================

def split_transcript(transcript: str) -> list:

    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=3000,
    #     chunk_overlap=200
    # )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    return splitter.split_text(transcript)


# ============================================================
# 📝 Summarize Transcript
# ============================================================

def summarize(transcript: str) -> str:

    llm = get_llm()

    # --------------------------------------------------------
    # Map Step
    # --------------------------------------------------------

    map_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Summarize this portion of a meeting transcript "
                "concisely."
            ),
            (
                "human",
                "{text}"
            )
        ]
    )

    map_chain = (
        map_prompt
        | llm
        | StrOutputParser()
    )

    chunks = split_transcript(transcript)

    chunk_summaries = [
        map_chain.invoke({"text": chunk})
        for chunk in chunks
    ]

    combined = "\n\n".join(chunk_summaries)

    # --------------------------------------------------------
    # Reduce Step
    # --------------------------------------------------------

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. "
                "Combine these partial summaries into one "
                "final professional meeting summary using "
                "clear bullet points."
            ),
            (
                "human",
                "{text}"
            )
        ]
    )

    combined_chain = (
        combined_prompt
        | llm
        | StrOutputParser()
    )

    return combined_chain.invoke(
        {"text": combined}
    )


# ============================================================
# 📌 Generate Meeting Title
# ============================================================

def generate_title(transcript: str) -> str:

    llm = get_llm()

    title_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Based on the meeting transcript, generate "
                "a short professional meeting title. "
                "Maximum 8 words. "
                "Return only the title and nothing else."
            ),
            (
                "human",
                "{text}"
            )
        ]
    )

    title_chain = (
        title_prompt
        | llm
        | StrOutputParser()
    )

    return title_chain.invoke(
        {"text": transcript[:2000]}
    )
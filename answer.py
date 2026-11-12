"""Answer a question from retrieved chunks, citing each chunk it used as [n]."""
import re
import sys

NOT_IN_DOCS = "Not in the docs."

INSTRUCTIONS = f"""You answer questions for on-call engineers using only the runbook excerpts below.
After every statement, cite the excerpt it came from, like [1] or [2].
If the excerpts do not contain the answer, reply exactly: {NOT_IN_DOCS}
Be brief."""


def build_prompt(question, chunks):
    excerpts = "\n\n".join(
        f"[{number}] {c['heading']}\n{c['text']}" for number, c in enumerate(chunks, start=1)
    )
    return f"{INSTRUCTIONS}\n\nExcerpts:\n\n{excerpts}\n\nQuestion: {question}"


def cited(answer_text, chunks):
    sources = []
    # Models write [1][4] or [1, 4]; read the numbers out of every bracket group.
    for group in re.findall(r"\[([\d,\s]+)\]", answer_text):
        for number in re.findall(r"\d+", group):
            position = int(number) - 1
            if 0 <= position < len(chunks) and chunks[position] not in sources:
                sources.append(chunks[position])
    return sources


def answer(question, chunks, llm):
    if not chunks:  # nothing was retrieved, so there is nothing to ground an answer in
        return {"answer": NOT_IN_DOCS, "sources": []}
    text = llm.invoke(build_prompt(question, chunks)).content
    return {"answer": text, "sources": cited(text, chunks)}


if __name__ == "__main__":
    import httpx
    from langchain_ollama import ChatOllama

    from rerank import rerank
    from search import hybrid_search, load

    question = sys.argv[1]
    chunks, index = load()
    top = rerank(question, hybrid_search(chunks, index, question, k=20))
    try:
        result = answer(question, top, ChatOllama(model="llama3.2", temperature=0))
    except httpx.ConnectError:
        sys.exit("Ollama is not running. Start it with: ollama serve")
    print(result["answer"], "\n\nSources:")
    for chunk in result["sources"]:
        print(f"  [{top.index(chunk) + 1}] {chunk['id']}  ({chunk['heading']})")

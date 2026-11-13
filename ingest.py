"""Turn a folder of markdown runbooks into small labelled chunks, saved as chunks.jsonl."""
import json
import re
import sys
from pathlib import Path

from langchain_text_splitters import MarkdownHeaderTextSplitter

# shortcut: sections are not split further by size; the longest runbook section is 1,705
# characters. Add a size-based splitter when a corpus has sections over about 2,000.
splitter = MarkdownHeaderTextSplitter([("#", "h1"), ("##", "h2"), ("###", "h3")])

# The "--- title: ... ---" block at the top of a file is site config, not content.
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def chunk_markdown(text, source):
    sections = splitter.split_text(FRONT_MATTER.sub("", text))
    chunks = []
    for position, section in enumerate(sections):
        if section.page_content.strip().upper() == "TODO":
            continue
        chunks.append({
            "id": f"{source}#{position}",
            "source": source,
            "heading": " > ".join(section.metadata.values()),
            "text": section.page_content,
        })
    return chunks


def ingest(root):
    root = Path(root)
    chunks = []
    for path in sorted(root.rglob("*.md")):
        chunks += chunk_markdown(path.read_text(), path.relative_to(root).as_posix())
    if not chunks:
        sys.exit(f"No markdown files with content found in {root}")
    return chunks


if __name__ == "__main__":
    chunks = ingest(sys.argv[1])
    with open("chunks.jsonl", "w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")
    files = {chunk["source"] for chunk in chunks}
    print(f"{len(chunks)} chunks from {len(files)} files -> chunks.jsonl")

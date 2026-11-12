from ingest import chunk_markdown, ingest

# A small runbook in the same shape as the real ones: front matter, one alert, sections.
RUNBOOK = """---
title: Kube Pod Crash Looping
weight: 20
---

# KubePodCrashLooping

## Meaning

Pod is in CrashLoop.

## Diagnosis

Check the logs:

```bash
# show logs of the previous container
kubectl logs $POD --previous
```
"""


def test_heading_names_the_alert_and_the_section():
    chunks = chunk_markdown(RUNBOOK, source="a.md")
    assert [c["heading"] for c in chunks] == [
        "KubePodCrashLooping > Meaning",
        "KubePodCrashLooping > Diagnosis",
    ]


def test_front_matter_is_not_chunk_text():
    chunks = chunk_markdown(RUNBOOK, source="a.md")
    assert not any("weight: 20" in c["text"] for c in chunks)


def test_hash_comment_inside_a_code_block_is_not_a_heading():
    chunks = chunk_markdown(RUNBOOK, source="a.md")
    assert "# show logs of the previous container" in chunks[-1]["text"]


def test_chunk_id_is_source_plus_position():
    chunks = chunk_markdown(RUNBOOK, source="kubernetes/KubePodCrashLooping.md")
    assert [c["id"] for c in chunks] == [
        "kubernetes/KubePodCrashLooping.md#0",
        "kubernetes/KubePodCrashLooping.md#1",
    ]


def test_ingest_uses_the_path_inside_the_corpus_as_source(tmp_path):
    (tmp_path / "node").mkdir()
    (tmp_path / "node" / "NodeDown.md").write_text(RUNBOOK)
    chunks = ingest(tmp_path)
    assert {c["source"] for c in chunks} == {"node/NodeDown.md"}

def test_section_with_only_todo_is_skipped():
    text = """# NodeDown

## Meaning

Node is not reachable.

## Mitigation

TODO
"""
    chunks = chunk_markdown(text, source="a.md")
    assert [c["heading"] for c in chunks] == ["NodeDown > Meaning"]

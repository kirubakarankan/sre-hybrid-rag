from langchain_core.language_models.fake_chat_models import FakeListChatModel

from answer import NOT_IN_DOCS, answer, build_prompt, cited
from tests.test_search import CHUNKS


def test_prompt_numbers_each_chunk_and_shows_its_heading_and_text():
    prompt = build_prompt("why?", CHUNKS[:2])
    assert "[1] KubePodCrashLooping > Meaning\nPod is restarting again and again." in prompt
    assert "[2] NodeFilesystemAlmostOutOfSpace > Meaning" in prompt


def test_cited_returns_the_chunks_the_answer_points_to_once_each_in_order():
    assert cited("Free some space [2]. The pod restarts [1][2].", CHUNKS) == [CHUNKS[1], CHUNKS[0]]


def test_cited_ignores_a_number_that_matches_no_chunk():
    assert cited("See [9] and [0].", CHUNKS) == []


def test_answer_returns_the_model_text_and_its_sources():
    llm = FakeListChatModel(responses=["The pod is restarting [1]."])
    result = answer("what is wrong?", CHUNKS, llm)
    assert result == {"answer": "The pod is restarting [1].", "sources": [CHUNKS[0]]}


def test_answer_without_chunks_does_not_ask_the_model():
    llm = FakeListChatModel(responses=["I made something up."])
    assert answer("what is wrong?", [], llm) == {"answer": NOT_IN_DOCS, "sources": []}


def test_cited_reads_several_numbers_inside_one_pair_of_brackets():
    assert cited("Check the probes [1, 4].", CHUNKS) == [CHUNKS[0], CHUNKS[3]]

from evals.run_evals import reciprocal_rank

RESULTS = [{"source": "a.md"}, {"source": "b.md"}, {"source": "b.md"}]


def test_reciprocal_rank_is_one_over_the_position_of_the_first_chunk_from_the_right_runbook():
    assert reciprocal_rank(RESULTS, "b.md") == 1 / 2


def test_reciprocal_rank_is_zero_when_the_right_runbook_is_not_in_the_results():
    assert reciprocal_rank(RESULTS, "z.md") == 0

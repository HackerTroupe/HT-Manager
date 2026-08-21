from types import SimpleNamespace

from ht_manager.jobs.poll_close import _ctf_by_answer_id


def test_ctf_mapping_uses_discord_answer_ids() -> None:
    options = [
        SimpleNamespace(option_index=0, ctf_id=14),
        SimpleNamespace(option_index=1, ctf_id=9),
    ]

    assert _ctf_by_answer_id(options) == {1: 14, 2: 9}
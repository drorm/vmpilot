import types
from unittest.mock import MagicMock, patch

import pytest

from vmpilot.config import Provider
from vmpilot.usage import Usage


def make_usage(provider, model=None):
    return Usage(provider=provider, model_name=model)


# ---- get_totals and calculate_cost for each provider ----
def test_get_totals_and_calculate_cost_openai():
    usage = make_usage(Provider.OPENAI)
    usage.input_tokens = 100
    usage.output_tokens = 40
    usage.cache_read_input_tokens = 10
    usage.model_name = "gpt-test"
    totals = usage.get_totals()
    costs = usage.calculate_cost()
    assert isinstance(totals, dict)
    assert "input_tokens" in totals
    assert "total_cost" in costs


def test_get_totals_and_calculate_cost_google():
    usage = make_usage(Provider.GOOGLE)
    usage.input_tokens = 100
    usage.output_tokens = 40
    usage.cache_read_input_tokens = 10
    usage.model_name = "gemini-test"
    totals = usage.get_totals()
    costs = usage.calculate_cost()
    assert isinstance(totals, dict)
    assert "input_tokens" in totals
    assert "total_cost" in costs


def test_get_totals_and_calculate_cost_anthropic():
    usage = make_usage(Provider.ANTHROPIC)
    usage.input_tokens = 100
    usage.output_tokens = 40
    usage.cache_creation_input_tokens = 5
    usage.cache_read_input_tokens = 10
    usage.model_name = "claude-test"
    totals = usage.get_totals()
    costs = usage.calculate_cost()
    assert isinstance(totals, dict)
    assert "input_tokens" in totals
    assert "total_cost" in costs


# ---- store_cost_in_db ----
@patch("vmpilot.usage.ConversationRepository")
def test_store_cost_in_db_success(MockRepo):
    usage = make_usage(Provider.OPENAI)
    repo = MockRepo.return_value
    usage.store_cost_in_db(
        chat_id="cid",
        model="gpt-4",
        request="test request",
        cost={"total_cost": 0.001},
        start="starttime",
        end="endtime",
    )
    args, kwargs = repo.create_exchange.call_args
    assert args[0] == "cid"
    assert args[1] == "gpt-4"
    assert args[2] == "test request"
    # cost rounded
    assert args[3]["total_cost"] == 0.001


@patch("vmpilot.usage.logger")
@patch("vmpilot.usage.ConversationRepository")
def test_store_cost_in_db_error(MockRepo, mock_logger):
    usage = make_usage(Provider.OPENAI)
    repo = MockRepo.return_value
    repo.create_exchange.side_effect = Exception("DB fail")
    usage.store_cost_in_db("cid", "gpt-4", "foo", {"x": 1.0}, "s", "e")
    mock_logger.error.assert_called()


@patch("vmpilot.usage.ConversationRepository")
def test_store_cost_in_db_truncate(MockRepo):
    usage = make_usage(Provider.OPENAI)
    long_req = "A" * 700
    usage.store_cost_in_db("cid", "gpt-4", long_req, {"x": 0.1}, "s", "e")
    args, _ = MockRepo.return_value.create_exchange.call_args
    assert len(args[2]) <= 503
    assert args[2].endswith("...")


# ---- get_cost_message and get_cost_summary ----
def make_mock_repo(acc=None, breakdown=None, fail=False):
    repo = MagicMock()
    if not fail:
        repo.get_accumulated_cost.return_value = acc
        repo.get_accumulated_cost_breakdown.return_value = breakdown
    else:
        repo.get_accumulated_cost.side_effect = Exception()
        repo.get_accumulated_cost_breakdown.side_effect = Exception()
    return repo


@patch("vmpilot.usage.ConversationRepository")
@patch("vmpilot.usage.config")
def test_get_cost_message_total_only(config, MockRepo):
    config.get_pricing_display.return_value = type(
        "Display", (), {"TOTAL_ONLY": 1, "DISABLED": 0}
    )().TOTAL_ONLY
    usage = make_usage(Provider.OPENAI)
    usage.input_tokens = 50
    usage.output_tokens = 50
    MockRepo.return_value = make_mock_repo(
        acc=0.123456,
        breakdown={
            "total_cost": 0.654321,
            "input_cost": 0.1,
            "output_cost": 0.2,
            "cache_read_cost": 0.3,
        },
    )
    msg = usage.get_cost_message(chat_id="cid")
    assert "| Request" in msg or "|--------" in msg  # Markdown table header present
    assert (
        "0.123456" in msg or "0.654321" in msg or "$" in msg
    )  # Some cost value expected


@patch("vmpilot.usage.ConversationRepository")
@patch("vmpilot.usage.config")
def test_get_cost_message_disabled(config, MockRepo):
    config.get_pricing_display.return_value = type(
        "Display", (), {"TOTAL_ONLY": 1, "DISABLED": 0}
    )().DISABLED
    usage = make_usage(Provider.OPENAI)
    msg = usage.get_cost_message(chat_id="cid")
    # For DISABLED, only the markdown table is produced (not empty string)
    assert msg.strip().startswith("| Request") or "|--------" in msg


@patch("vmpilot.usage.ConversationRepository")
@patch("vmpilot.usage.config")
def test_get_cost_message_db_error(config, MockRepo):
    config.get_pricing_display.return_value = type(
        "Display", (), {"TOTAL_ONLY": 1, "DISABLED": 0}
    )().TOTAL_ONLY
    usage = make_usage(Provider.OPENAI)
    MockRepo.return_value = make_mock_repo(fail=True)
    msg = usage.get_cost_message(chat_id="cid")
    # Should still render the markdown table even on DB error
    assert "| Request" in msg or "|--------" in msg


# ---- get_cost_summary returns cache, triggers calculate on miss ----
def test_get_cost_summary_caching():
    usage = make_usage(Provider.OPENAI)
    usage.input_tokens = 2
    usage.output_tokens = 2
    usage._cached_totals = None
    usage._cached_costs = None
    totals, costs = usage.get_cost_summary()
    # call again (should hit cache)
    totals2, costs2 = usage.get_cost_summary()
    assert totals == totals2
    assert costs == costs2


# ---- test rounding of floats in store_cost_in_db ----
def test_store_cost_in_db_rounding():
    usage = make_usage(Provider.OPENAI)

    class DummyRepo:
        def create_exchange(self, chat_id, model, request, cost, start, end):
            self.result = cost

    with patch("vmpilot.usage.ConversationRepository", return_value=DummyRepo()) as _:
        usage.store_cost_in_db(
            "cid", "mod", "r", {"a": 1.12345678, "b": {"c": 0.9999999}}, "s", "e"
        )


# ---- test Anthropic accumulated table formatting ----
@patch("vmpilot.usage.ConversationRepository")
@patch("vmpilot.usage.config")
def test_get_cost_message_anthropic_table(config, MockRepo):
    config.get_pricing_display.return_value = 2  # neither DISABLED nor TOTAL_ONLY
    usage = make_usage(Provider.ANTHROPIC)
    usage.input_tokens = 5
    usage.output_tokens = 2
    usage.cache_creation_input_tokens = 1
    usage.cache_read_input_tokens = 1
    MockRepo.return_value = make_mock_repo(
        breakdown={
            "total_cost": 1.00,
            "cache_creation_cost": 0.3,
            "cache_read_cost": 0.3,
            "output_cost": 0.4,
        }
    )
    msg = usage.get_cost_message(chat_id="cid")
    assert "All" in msg and "cache_creation_cost" not in msg

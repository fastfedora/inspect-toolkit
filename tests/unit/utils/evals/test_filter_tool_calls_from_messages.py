from inspect_ai.model import ChatMessageAssistant, ChatMessageTool, ChatMessageUser
from inspect_ai.tool import ToolCall

from inspect_toolkit.utils.evals import filter_tool_calls_from_messages


def tool_call(id: str, function: str) -> ToolCall:
    return ToolCall(id=id, function=function, arguments={})


class TestFilterToolCallsFromMessages:
    def test_removes_named_tool_call_and_its_result_message(self):
        messages = [
            ChatMessageAssistant(
                content="",
                tool_calls=[tool_call("1", "foo"), tool_call("2", "bar")],
            ),
            ChatMessageTool(content="foo-result", tool_call_id="1"),
            ChatMessageTool(content="bar-result", tool_call_id="2"),
        ]

        result = filter_tool_calls_from_messages(messages, exclude=["foo"])

        # The assistant keeps only `bar`, and only `bar`'s result message survives.
        assert [type(m).__name__ for m in result] == ["ChatMessageAssistant", "ChatMessageTool"]
        assert [tc.function for tc in result[0].tool_calls] == ["bar"]
        assert result[1].tool_call_id == "2"

    def test_keeps_unrelated_messages_unchanged(self):
        user = ChatMessageUser(content="hello")
        assistant = ChatMessageAssistant(content="hi", tool_calls=[tool_call("1", "bar")])
        tool = ChatMessageTool(content="bar-result", tool_call_id="1")

        result = filter_tool_calls_from_messages([user, assistant, tool], exclude=["foo"])

        assert result == [user, assistant, tool]

    def test_assistant_with_content_is_kept_when_all_calls_removed(self):
        messages = [
            ChatMessageAssistant(content="some reasoning", tool_calls=[tool_call("1", "foo")]),
            ChatMessageTool(content="foo-result", tool_call_id="1"),
        ]

        result = filter_tool_calls_from_messages(messages, exclude=["foo"])

        # Assistant kept (it has content), tool calls cleared, orphaned tool result dropped.
        assert len(result) == 1
        assert isinstance(result[0], ChatMessageAssistant)
        assert result[0].tool_calls is None

    def test_assistant_with_no_content_and_all_calls_removed_is_dropped(self):
        messages = [
            ChatMessageAssistant(content="", tool_calls=[tool_call("1", "foo")]),
            ChatMessageTool(content="foo-result", tool_call_id="1"),
        ]

        result = filter_tool_calls_from_messages(messages, exclude=["foo"])

        assert result == []

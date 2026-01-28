from __future__ import annotations

from typing import Any

from funpaybotengine.dispatching.events import NewMessageEvent

from funpayhub.app.properties import FunPayHubProperties


def is_fph_command(
    event: NewMessageEvent,
    properties: FunPayHubProperties,
) -> bool | dict[str, Any]:
    if not event.message.text:
        return False

    text = event.message.text

    for command, params in properties.auto_response.entries.items():
        if not params.case_sensitive.value:
            command = command.casefold()
            text = event.message.text.casefold()

        if not text.startswith(command + ' ') and text != command:
            continue

        if not params.react_on_me.value and event.message.from_me:
            return False
        if not params.react_on_others.value and not event.message.from_me:
            return False

        if not any(
            [
                params.reply.value and params.response_text.value,
                params.hooks.value,
            ],
        ):
            return False
        return {'command': params}
    return False

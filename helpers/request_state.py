_HELP_REQUESTED = set()


def mark_help_requested(channel_id):
    _HELP_REQUESTED.add(channel_id)


def help_requested(channel_id):
    return channel_id in _HELP_REQUESTED


def clear_request_state(channel_id):
    _HELP_REQUESTED.discard(channel_id)

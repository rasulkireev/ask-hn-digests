import structlog


def get_ask_hn_digest_logger(name):
    """This will add a `ask_hn_digest` prefix to logger for easy configuration."""

    return structlog.get_logger(
        f"ask_hn_digest.{name}",
        project="ask_hn_digest"
    )

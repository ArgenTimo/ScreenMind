"""Bind .env hotkey names to :class:`pynput.keyboard.Key` using the caller's keyboard module."""


def bind_key(keyboard_mod, spec: str, default: str):
    """
    Resolve ``f8``, ``scroll_lock``, etc. via the **same** ``keyboard`` object the listener uses.

    A separate ``from pynput import keyboard`` elsewhere can load keys that do not compare equal
    to events from :class:`pynput.keyboard.Listener`, so callers must pass ``keyboard`` from their
    own import.
    """
    raw = (spec if spec else default) or default
    name = str(raw).strip().lower().replace(" ", "_").replace("-", "_")
    if not name:
        name = default.strip().lower()

    key = getattr(keyboard_mod.Key, name, None)
    if key is None:
        raise ValueError(
            f"Unknown hotkey '{raw}'. "
            "Use a pynput keyboard.Key name (f1–f20, scroll_lock, esc, …). "
            "See https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key"
        )
    return key

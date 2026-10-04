"""The client's last word: every way it ends leaves a line saying why —
work order 213.

Data's client died as a battle opened (4 October 2026) and his terminal
showed nothing but the launcher stopping the engine: a SIGSEGV ends a Python
process before it can print anything, and nothing else said how the client
had ended. The cause was found from the core dump (`core/framerate._window`);
this module is what lets the next one be found from the terminal.

  a fatal signal      (SIGSEGV, SIGFPE, SIGABRT, SIGBUS, SIGILL) — Python's
                      `faulthandler`: "Fatal Python error: Segmentation
                      fault" and the stack of every thread
  an error            Python's traceback, then "ended: an error: <type>:
                      <message>"
  SIGTERM, SIGHUP     "ended: signal SIGTERM"
  Ctrl+C              "ended: interrupted (Ctrl+C)"
  a normal end        "ended: <reason>" — the window closed, the game ended
                      at the player's request (`ended()` names it)
  SIGKILL             nothing can run in the process; `play.py` says it
                      (`play.ending`), as it says every way its client ended
"""
import atexit
import faulthandler
import logging
import signal
import sys

log = logging.getLogger("orionlayer")

#: what `_at_exit` reports; `ended()` sets it, the first reason wins
_reason = None
_installed = False


def ended(reason):
    """Name why the client is ending; the first reason given is the one."""
    global _reason
    if _reason is None:
        _reason = reason


def _on_signal(signum, _frame):
    ended(f"signal {signal.Signals(signum).name}")
    raise SystemExit(128 + signum)


def _excepthook(kind, value, tb, previous=sys.excepthook):
    previous(kind, value, tb)
    if issubclass(kind, KeyboardInterrupt):
        ended("interrupted (Ctrl+C)")
    else:
        ended(f"an error: {kind.__name__}: {value}")


def _at_exit():
    log.info("ended: %s", _reason or "the program returned without a reason")


def install():
    """Once, at the start of `main.App`."""
    global _installed
    if _installed:
        return
    _installed = True
    faulthandler.enable(file=sys.stderr, all_threads=True)
    sys.excepthook = _excepthook
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _on_signal)
    # after `logging`'s own exit handler, so it runs first (LIFO) and the
    # line is written while the handlers still stand
    atexit.register(_at_exit)

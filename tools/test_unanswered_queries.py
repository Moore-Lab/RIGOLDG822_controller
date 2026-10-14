"""Every query the front ends send must be one the DG822 actually answers.

A query the instrument does not recognise is not answered at all: the DG822
queues a -113 error and sends nothing, so the host waits out the whole VISA
timeout (5 s) before giving up. That is how :SOURce<n>:FUNCtion:ARBitrary? -- a
header the DG800 does not have -- made every web-page refresh take 10.0 s on
the bench (two channels, one timeout each) while holding the session lock, so an
"output on" click queued for up to the same again.

The simulator records every query it would have left unanswered
(``SimulatedDG822.unanswered``). This test drives the same paths the web page
and the CLI use and asserts that list stays empty.

Run: python tools/test_unanswered_queries.py     (needs no VISA implementation)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np                                   # noqa: E402

from rigol_dg822 import SIM_RESOURCE, DG822Controller  # noqa: E402
from rigol_dg822.webapp import DG822Session, start, stop  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name:52s} {detail}")
    if not ok:
        FAILS.append(name)


def sim_of(controller):
    """The simulated instrument, with its records reset for this test.

    Every connection in a process shares one SimulatedDG822 (it models one
    physical box), so what an earlier test left behind would otherwise be
    blamed on this one.
    """
    sim = controller.connection._instrument
    sim.unanswered.clear()
    sim.clear()                                     # empties the error queue
    return sim


def t_web_paths():
    """The web page's poll and every write endpoint's read-back."""
    s = DG822Session(simulate=True)
    start(s)
    sim = sim_of(s.controller)
    try:
        s.state()                                     # the 1 s poll: both channels
        s.apply(1, {"waveform": "square", "frequency": 1000, "amplitude": 1.0,
                    "duty_cycle": 25})
        s.set_params(2, {"frequency": 2000})
        s.set_load(1, 50)
        s.set_polarity(1, True)
        s.set_sync(2, True)
        s.set_output(1, True)
        s.set_output(1, False)
        s.upload_arb(2, np.sin(np.linspace(0, 2 * np.pi, 1024)), name="T",
                     frequency=1000.0, amplitude=1.0, offset=0.0)
        s._invalidate()
        s.state()
        check("web poll + writes: no unanswered query", sim.unanswered == [],
              ", ".join(sim.unanswered))
        check("web poll + writes: error queue clean", sim.errors == [],
              "; ".join(m for _, m in sim.errors))
    finally:
        stop(s)


def t_cli_status():
    """`rigol-cli status` reads every parameter on both channels."""
    from rigol_dg822.cli import _channel_state
    dg = DG822Controller(SIM_RESOURCE)
    assert dg.connect()
    sim = sim_of(dg)
    try:
        for ch in (1, 2):
            state = _channel_state(dg, ch)
        check("cli status: no unanswered query", sim.unanswered == [],
              ", ".join(sim.unanswered))
        check("cli status: idle level reads back", state.get("idle") == "FPT",
              f"got {state.get('idle')!r}")
    finally:
        dg.disconnect()


def t_sim_catches_the_bug():
    """The guard itself: the query that caused the 10 s poll must be caught."""
    dg = DG822Controller(SIM_RESOURCE)
    assert dg.connect()
    sim = sim_of(dg)
    try:
        reply = dg.connection.query(":SOURce1:FUNCtion:ARBitrary?")
        check("sim leaves a non-existent query unanswered", reply is None,
              f"got {reply!r}")
        check("  ... and records it", sim.unanswered == [":SOURce1:FUNCtion:ARBitrary?"],
              repr(sim.unanswered))
        check("  ... and queues -113 like the instrument",
              any(code == -113 for code, _ in sim.errors))
    finally:
        dg.disconnect()


for fn in (t_web_paths, t_cli_status, t_sim_catches_the_bug):
    print(f"\n-- {fn.__name__} --")
    fn()

print("\n" + ("ALL PASS" if not FAILS else f"FAILED: {', '.join(FAILS)}"))
sys.exit(1 if FAILS else 0)

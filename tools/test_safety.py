"""Regression tests for the failures that can leave an output driving.

Every case here was a real defect found by review, not a hypothetical. They are
grouped together because they share one consequence: the DG822 keeps driving the
experiment when the software believes it does not, or the page shows a level the
instrument is not emitting.

Run: python tools/test_safety.py     (needs no VISA implementation)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rigol_dg822.webapp import (           # noqa: E402
    MAX_RUN_SECONDS, DG822Session, create_app, start, stop)

FAILS = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name:44s} {detail}")
    if not ok:
        FAILS.append(name)


def sim_session():
    s = DG822Session(simulate=True)
    start(s)
    assert s.ok, s.error
    return s, s.controller.connection._instrument


def t_timer_ceiling():
    """An unschedulable duration must be refused, not accepted and dropped.

    threading.Timer silently dies past _thread.TIMEOUT_MAX (~49.7 days), leaving
    the output enabled with nothing to switch it off.
    """
    s, sim = sim_session()
    try:
        try:
            s.set_output(1, True, seconds=MAX_RUN_SECONDS + 1)
            check("over-ceiling seconds refused", False, "no ValueError raised")
        except ValueError:
            check("over-ceiling seconds refused", True,
                  f"and output left {'ON - BAD' if sim.channels[1].output else 'off'}")
            check("  ... and the output stayed off", not sim.channels[1].output)
        # the cycles path reaches the same ceiling by division
        s.set_params(1, {"frequency": 1e-6})
        try:
            s.set_output(1, True, cycles=1000)
            check("over-ceiling cycles refused", False, "no ValueError raised")
        except ValueError:
            check("over-ceiling cycles refused", True)
        # a normal run still works
        s.set_params(1, {"frequency": 1000})
        s.set_output(1, True, seconds=5)
        check("ordinary timed run still arms", s._timers.get(1) is not None
              and s._timers[1].is_alive())
    finally:
        stop(s)


def t_connect_does_not_orphan():
    """Switching instruments must not leave a timed run driving the old one."""
    s, sim = sim_session()
    try:
        s.set_output(1, True, seconds=600)
        assert sim.channels[1].output, "setup failed"
        s.connect(simulate=True)              # rebind; old instrument unreachable
        check("connect() switches a timed output off", not sim.channels[1].output,
              "was left driving" if sim.channels[1].output else "")
    finally:
        stop(s)


def t_stop_clears_outputs():
    """Shutdown must drop both outputs and cancel pending timers."""
    s, sim = sim_session()
    s.set_output(1, True)
    s.set_output(2, True, seconds=600)
    stop(s)
    check("stop() switches both outputs off",
          not sim.channels[1].output and not sim.channels[2].output)
    check("stop() cancels pending timers",
          all(not (t and t.is_alive()) for t in s._timers.values()))


def t_sync_reads_back():
    """:OUTPut:SYNC? answers ON/OFF per the programming guide, not 1/0."""
    s, _ = sim_session()
    try:
        raw = s.controller.connection.query(":OUTPut1:SYNC?")
        check("sim answers SYNC? with ON/OFF", raw.strip().upper() in ("ON", "OFF"),
              f"got {raw.strip()!r}")
        s.set_sync(1, True)
        check("driver reads an enabled sync back as True",
              s.controller.output.get_sync_state(1) is True)
    finally:
        stop(s)


def t_arb_switches_to_user():
    """A DAC16 upload must leave the channel in an arbitrary mode."""
    import numpy as np
    s, _ = sim_session()
    try:
        n = 4096
        data = np.sin(np.linspace(0, 2 * np.pi, n))
        s.upload_arb(1, data, name="T", frequency=2000.0, amplitude=2.0, offset=0.0)
        ch = s.read_channel(1)
        check("arb upload switches the channel to USER",
              "USER" in (ch.get("function_raw") or "").upper(),
              f"got {ch.get('function_raw')!r}")
        check("arb sample rate is frequency x points",
              ch.get("sample_rate") == 2000.0 * n,
              f"got {ch.get('sample_rate')} want {2000.0 * n}")
    finally:
        stop(s)


def t_limit_warnings():
    """An unachievable setting must be reported, since the DG822 clamps silently."""
    s, _ = sim_session()
    try:
        s.apply(1, {"waveform": "sine", "frequency": 1000,
                    "amplitude": 20.0, "offset": 20.0})
        w = s.channel(1)["warnings"]
        check("over-rail amplitude+offset warns", any("rail" in x for x in w),
              f"{len(w)} warning(s)")
        s.apply(1, {"waveform": "sine", "frequency": 9e12, "amplitude": 1.0})
        check("out-of-range frequency warns",
              any("frequency" in x for x in s.channel(1)["warnings"]))
        s.apply(1, {"waveform": "sine", "frequency": 1000,
                    "amplitude": 1.0, "offset": 0.0})
        check("a legal setting warns about nothing", s.channel(1)["warnings"] == [])
    finally:
        stop(s)


for fn in (t_timer_ceiling, t_connect_does_not_orphan, t_stop_clears_outputs,
           t_sync_reads_back, t_arb_switches_to_user, t_limit_warnings):
    print(f"\n-- {fn.__name__} --")
    fn()

print("\n" + ("ALL PASS" if not FAILS else f"FAILED: {', '.join(FAILS)}"))
sys.exit(1 if FAILS else 0)

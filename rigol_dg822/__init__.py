"""rigol_dg822: RIGOL DG822/DG800 function generator control.

The high-level entry point is :class:`~rigol_dg822.controller.DG822Controller`,
which owns a :class:`~rigol_dg822.connection.DG822Connection` and lazily builds
:class:`~rigol_dg822.waveform.DG822Waveform` and
:class:`~rigol_dg822.output.DG822Output` on a successful connect. Arbitrary
waveform synthesis and the DG822 file formats live in
:mod:`rigol_dg822.arbitrary`; preview maths and plotting in
:mod:`rigol_dg822.plot` (headless-safe -- no tkinter at import).

:mod:`rigol_dg822.sim` is a simulated DG822 that presents the pyvisa resource
interface, so everything above the connection layer runs with no VISA
implementation installed::

    from rigol_dg822 import DG822Controller, SIM_RESOURCE

    dg = DG822Controller(SIM_RESOURCE)
    dg.connect()
    dg.setup_sine(1, frequency=2500.0, amplitude=1.0)
    dg.output_on(1)

Swap SIM_RESOURCE for a real 'USB0::0x1AB1::0x0643::...::INSTR' string, or call
``dg.auto_connect()``, to drive the instrument itself. Nothing in this package
raises on a missing instrument or a missing VISA backend -- it degrades to a
marked "unavailable" state so a panel embedding it stays up.

The tkinter desktop GUI is ``dg822_gui.py`` beside this package, not inside it:
the package must stay importable on a headless server.

``arbitrary`` and ``plot`` are deliberately not re-exported here -- they pull in
numpy and matplotlib, and a control path that only talks SCPI should not fail to
import because a plotting dependency is missing. Import them by module.
"""

from .connection import DG822Connection
from .controller import DG822Controller
from .output import DG822Output, OutputPolarity, SyncMode
from .waveform import DG822Waveform, WaveformType
from .sim import SIM_RESOURCE, SIM_IDN, SimulatedDG822, SimulatedResourceManager

__all__ = [
    "DG822Controller",
    "DG822Connection",
    "DG822Waveform",
    "WaveformType",
    "DG822Output",
    "OutputPolarity",
    "SyncMode",
    "SIM_RESOURCE",
    "SIM_IDN",
    "SimulatedDG822",
    "SimulatedResourceManager",
]

"""
qiskit_runner.py  —  Qiskit integration for ADC / Quantum Readout mode

Provides three things:
  1. run_readout_circuit()   — H+measure circuit, returns counts dict
  2. run_t1_circuit()        — T1 decay circuit (X + delay + measure)
  3. run_bell_circuit()      — 2-qubit Bell state, returns counts dict
  4. draw_circuit_ascii()    — text-art circuit diagram (no extra deps)
  5. QISKIT_AVAILABLE        — bool flag for conditional UI rendering

All functions have a pure-Python fallback so the app runs even if
qiskit / qiskit-aer are not installed (e.g. on Streamlit Cloud free tier
where RAM is limited).  The fallback uses a faithful statistical model
so readout plots stay physically meaningful.
"""

from __future__ import annotations
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# AVAILABILITY CHECK
# ─────────────────────────────────────────────────────────────────────────────
QISKIT_AVAILABLE = False
QISKIT_AER_AVAILABLE = False
_import_error: str = ""

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister  # type: ignore
    from qiskit.circuit.library import RZGate, RXGate  # type: ignore
    QISKIT_AVAILABLE = True
except ImportError as e:
    _import_error = str(e)

try:
    from qiskit_aer import AerSimulator  # type: ignore
    QISKIT_AER_AVAILABLE = True
except ImportError:
    try:
        from qiskit.providers.aer import AerSimulator  # type: ignore  (older API)
        QISKIT_AER_AVAILABLE = True
    except ImportError:
        pass


def get_status() -> dict:
    """Return a dict describing Qiskit availability for display in the UI."""
    return {
        "qiskit": QISKIT_AVAILABLE,
        "aer": QISKIT_AER_AVAILABLE,
        "error": _import_error,
        "mode": (
            "full"      if (QISKIT_AVAILABLE and QISKIT_AER_AVAILABLE) else
            "qiskit_only" if QISKIT_AVAILABLE else
            "fallback"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CIRCUIT BUILDERS  (only called when Qiskit is available)
# ─────────────────────────────────────────────────────────────────────────────
def _build_readout_circuit(fidelity: float) -> "QuantumCircuit":
    """H gate → optional RX error → measure.
    fidelity controls the RX rotation that mimics readout error.
    """
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    # Tiny RX rotation to model readout error (0 = perfect, π = total flip)
    error_angle = np.pi * (1.0 - fidelity) * 0.1
    qc.rx(error_angle, 0)
    qc.measure(0, 0)
    return qc


def _build_t1_circuit(delay_steps: int) -> "QuantumCircuit":
    """X → identity delays → measure  (T1 decay toy model)."""
    qc = QuantumCircuit(1, 1)
    qc.x(0)
    for _ in range(delay_steps):
        qc.id(0)          # identity = one time step
    qc.measure(0, 0)
    return qc


def _build_bell_circuit() -> "QuantumCircuit":
    """Standard Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2."""
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def _build_grover_circuit() -> "QuantumCircuit":
    """Grover oracle for 2-qubit search (marks |11⟩)."""
    qc = QuantumCircuit(2, 2)
    qc.h([0, 1])
    # Oracle: flip phase of |11⟩
    qc.cz(0, 1)
    # Diffuser
    qc.h([0, 1])
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])
    qc.measure([0, 1], [0, 1])
    return qc


def _simulate(qc: "QuantumCircuit", shots: int) -> dict:
    """Run circuit on AerSimulator or statevector fallback."""
    if QISKIT_AER_AVAILABLE:
        sim = AerSimulator()
        job = sim.run(qc, shots=shots)
        return job.result().get_counts()
    else:
        # Qiskit available but no Aer — use statevector
        from qiskit.quantum_info import Statevector  # type: ignore
        sv = Statevector.from_instruction(qc.remove_final_measurements(inplace=False))
        probs = sv.probabilities_dict()
        rng = np.random.default_rng(42)
        counts: dict[str, int] = {}
        for state, prob in probs.items():
            counts[state] = int(round(prob * shots))
        return counts


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK SIMULATORS  (no Qiskit at all)
# ─────────────────────────────────────────────────────────────────────────────
def _fallback_readout(fidelity: float, shots: int) -> dict:
    """Statistical model: H gate gives 50/50, fidelity biases it slightly."""
    rng = np.random.default_rng(42)
    p1 = 0.5 + (fidelity - 0.5) * 0.05   # readout error shifts p1 a little
    n1 = int(rng.binomial(shots, p1))
    return {"1": n1, "0": shots - n1}


def _fallback_t1(delay_steps: int, shots: int, t1_steps: int = 20) -> dict:
    """Exponential T1 decay: P(|1⟩) = exp(-delay/T1)."""
    p1 = float(np.exp(-delay_steps / max(t1_steps, 1)))
    rng = np.random.default_rng(42)
    n1 = int(rng.binomial(shots, p1))
    return {"1": n1, "0": shots - n1}


def _fallback_bell(shots: int) -> dict:
    """Bell state: only |00⟩ and |11⟩, each ~50%."""
    rng = np.random.default_rng(42)
    n11 = int(rng.binomial(shots, 0.5))
    return {"11": n11, "00": shots - n11}


def _fallback_grover(shots: int) -> dict:
    """Grover 2-qubit: |11⟩ should dominate after one iteration."""
    rng = np.random.default_rng(42)
    probs = {"11": 0.75, "00": 0.10, "01": 0.075, "10": 0.075}
    counts = {}
    remaining = shots
    for state, p in list(probs.items())[:-1]:
        n = int(rng.binomial(remaining, p / sum(probs.values())))
        counts[state] = n
        remaining -= n
    counts["10"] = remaining
    return counts


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────
def run_readout_circuit(fidelity: float, shots: int = 1000) -> dict:
    """Simulate H+measure qubit readout circuit. Returns counts dict."""
    if QISKIT_AVAILABLE:
        try:
            qc = _build_readout_circuit(fidelity)
            return _simulate(qc, shots)
        except Exception:
            pass
    return _fallback_readout(fidelity, shots)


def run_t1_circuit(delay_steps: int, shots: int = 1000, t1_steps: int = 20) -> dict:
    """Simulate T1 decay circuit. Returns counts dict."""
    if QISKIT_AVAILABLE:
        try:
            qc = _build_t1_circuit(delay_steps)
            return _simulate(qc, shots)
        except Exception:
            pass
    return _fallback_t1(delay_steps, shots, t1_steps)


def run_bell_circuit(shots: int = 1000) -> dict:
    """Simulate 2-qubit Bell state. Returns counts dict."""
    if QISKIT_AVAILABLE:
        try:
            qc = _build_bell_circuit()
            return _simulate(qc, shots)
        except Exception:
            pass
    return _fallback_bell(shots)


def run_grover_circuit(shots: int = 1000) -> dict:
    """Simulate 2-qubit Grover search. Returns counts dict."""
    if QISKIT_AVAILABLE:
        try:
            qc = _build_grover_circuit()
            return _simulate(qc, shots)
        except Exception:
            pass
    return _fallback_grover(shots)


def get_circuit_diagram(circuit_type: str, fidelity: float = 0.99,
                         delay_steps: int = 0) -> str:
    """Return a text-art circuit diagram string."""
    diagrams = {
        "readout": f"""\
┌───┐ ┌──────────────┐ ┌─┐
┤ H ├─┤ RX({np.pi*(1-fidelity)*0.1:.3f}) ├─┤M├
└───┘ └──────────────┘ └─┘
  q0: H → RX(ε) → Measure
  ε = π×(1−F)×0.1  where F = fidelity = {fidelity:.3f}""",

        "t1": f"""\
┌───┐ {'┌──┐ '*delay_steps}┌─┐
┤ X ├─{'┤id├─'*delay_steps}┤M├
└───┘ {'└──┘ '*delay_steps}└─┘
  q0: X → {"id × " + str(delay_steps) + " →" if delay_steps else "(no delay) →"} Measure
  Models T1 decay: P(|1⟩) ≈ exp(−delay/T1)""",

        "bell": """\
┌───┐      ┌─┐
┤ H ├──■───┤M├─── q0
└───┘┌─┴─┐ └─┘┌─┐
     ┤ X ├────┤M├ q1
     └───┘    └─┘
  q0: H → CNOT(ctrl) → Measure
  q1:      CNOT(tgt) → Measure
  Output: Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2""",

        "grover": """\
┌───┐ ┌──────────┐ ┌─┐
┤ H ├─┤          ├─┤M├ q0
├───┤ │  Grover  │ ├─┤
┤ H ├─┤  Oracle  ├─┤M├ q1
└───┘ └──────────┘ └─┘
  H⊗2 → CZ oracle (marks |11⟩) → Diffuser → Measure
  Amplifies |11⟩: P(|11⟩) ≈ 75% after 1 iteration""",
    }
    return diagrams.get(circuit_type, "Unknown circuit type")


def compute_t1_sweep(shots: int = 500, max_steps: int = 30) -> tuple:
    """Return (delay_steps_array, p1_array) for T1 decay curve."""
    steps = list(range(0, max_steps + 1, 2))
    p1_arr = []
    for d in steps:
        counts = run_t1_circuit(d, shots)
        total = sum(counts.values())
        p1_arr.append(counts.get("1", 0) / max(total, 1))
    return np.array(steps), np.array(p1_arr)

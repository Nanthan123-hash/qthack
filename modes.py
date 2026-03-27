"""
modes.py  —  ADC Analysis Platform
UI entry points for the three analysis modes:
  show_classical_ui()   — Classical ADC (7 sub-modes)
  show_quantum_ui()     — Quantum Readout
  show_comparison_ui()  — Side-by-side Comparison
"""

import numpy as np
import streamlit as st

import qiskit_runner as qr

from adc_processor import (
    quantize,
    quantize_with_dither,
    compute_snr,
    compute_enob,
    compute_thd,
    compute_sinad,
    detect_aliasing,
    compute_alias_frequency,
    oversample,
    downsample_quantized,
    downsample,
    snr_to_readout_error,
    compute_shot_noise_snr,
    combined_readout_snr,
    compute_dnl,
    compute_inl,
    compute_enob_vs_frequency,
)
from signal_generator import (
    generate_sine,
    generate_noisy_sine,
    generate_waveform,
    compute_fft,
    compute_psd,
    generate_iq_signal,
)
from plot_renderer import (
    PLOTLY_CONFIG,
    plot_standard,
    plot_oversampling,
    plot_aliasing,
    plot_realworld,
    plot_dithering,
    plot_quantum,
    plot_comparison,
    plot_fft_spectrum,
    plot_psd,
    plot_snr_sweep,
    plot_error_histogram,
)


# ─────────────────────────────────────────────────────────────────────────────
# CLASSICAL ADC — 7 sub-modes via tabs
# ─────────────────────────────────────────────────────────────────────────────
def show_classical_ui():
    st.markdown('<div style="padding:20px 28px 0">', unsafe_allow_html=True)
    st.markdown("""
<div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.1em;
     text-transform:uppercase;color:var(--c-teal);margin-bottom:6px">
  Classical ADC Analysis
</div>
<div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;
     color:var(--c-text);letter-spacing:-.03em;margin-bottom:4px">
  ADC Signal Chain Simulator
</div>
<div style="font-family:'DM Sans',sans-serif;font-size:13px;color:var(--c-text2);
     line-height:1.6;margin-bottom:16px">
  Full ADC pipeline: quantization, oversampling, aliasing, noise, dithering,
  spectral analysis, and advanced characterization — all in one place.
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "⚡ Standard ADC",
        "🔼 Oversampling",
        "🌀 Aliasing",
        "📡 Real-World Noise",
        "🎲 Dithering",
        "📈 Spectral Analysis",
        "🔬 Advanced Characterization",
    ])

    # ── Sidebar controls ──────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ADC Controls")
        bits = st.slider("Bit depth (N)", 1, 16, 8)
        freq = st.slider("Signal frequency (Hz)", 10, 5000, 440)
        sample_rate = st.select_slider(
            "Sample rate (Hz)",
            options=[1000, 2000, 4000, 8000, 16000, 44100, 48000],
            value=8000,
        )
        amplitude = st.slider("Amplitude", 0.1, 1.0, 0.9, 0.05)
        duration = st.slider("Duration (s)", 0.01, 0.5, 0.05, 0.01)
        oversample_factor = st.select_slider(
            "Oversample factor",
            options=[1, 2, 4, 8, 16, 32, 64],
            value=4,
        )
        noise_std = st.slider("Noise σ (V)", 0.0, 0.5, 0.05, 0.005)

    # ── Shared signal generation ──────────────────────────────────────────────
    alias_detected = detect_aliasing(freq, sample_rate)
    t, analog = generate_sine(freq, duration, sample_rate * oversample_factor, amplitude)
    t_s, sampled = generate_sine(freq, duration, sample_rate, amplitude)
    quantized = quantize(sampled, bits)
    error = quantized - sampled
    snr = compute_snr(sampled, quantized)
    enob = compute_enob(snr)

    # ── Tab 1: Standard ADC ───────────────────────────────────────────────────
    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SNR", f"{snr:.2f} dB")
        c2.metric("ENOB", f"{enob:.2f} bits")
        c3.metric("Bit depth", f"{bits} bits")
        c4.metric("Theoretical SNR", f"{6.02*bits+1.76:.2f} dB")

        fig = plot_standard(t, analog, t_s, sampled, quantized, error, bits=bits)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        with st.expander("Quantization error histogram"):
            fig_h = plot_error_histogram(error, bits)
            st.plotly_chart(fig_h, use_container_width=True, config=PLOTLY_CONFIG)

        with st.expander("SNR vs bit depth sweep"):
            bits_range = list(range(1, 17))
            snr_theory = [6.02 * b + 1.76 for b in bits_range]
            snr_sim = []
            for b in bits_range:
                _, s = generate_sine(freq, duration, sample_rate, amplitude)
                q = quantize(s, b)
                snr_sim.append(compute_snr(s, q))
            fig_snr = plot_snr_sweep(bits_range, snr_sim, snr_theory)
            st.plotly_chart(fig_snr, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Tab 2: Oversampling ───────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("**Oversampling** — upsample → quantize → decimate. SNR gain = 10·log₁₀(M)/2 dB")
        over_sig, actual_factor = oversample(analog, oversample_factor)
        q_over = quantize(over_sig, bits)
        dec_sig = downsample_quantized(q_over, actual_factor)

        # Align lengths
        min_len = min(len(t_s), len(dec_sig))
        t_aligned = t_s[:min_len]
        q_normal = quantize(sampled[:min_len], bits)
        q_dec = dec_sig[:min_len]

        snr_normal = compute_snr(sampled[:min_len], q_normal)
        snr_over = compute_snr(sampled[:min_len], q_dec)
        expected_gain = 10 * np.log10(actual_factor) / 2

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SNR (1×)", f"{snr_normal:.1f} dB")
        c2.metric(f"SNR ({actual_factor}×)", f"{snr_over:.1f} dB")
        c3.metric("Actual gain", f"+{snr_over - snr_normal:.1f} dB")
        c4.metric("Theoretical gain", f"+{expected_gain:.1f} dB")

        fig = plot_oversampling(t_aligned, q_normal, q_dec,
                                snr_normal, snr_over, sampled[:min_len])
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Tab 3: Aliasing ───────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("**Aliasing** — signal above Nyquist folds back to a lower alias frequency.")
        alias_freq = compute_alias_frequency(freq, sample_rate)

        t_hi, sig_hi = generate_sine(freq, duration, max(sample_rate * 8, 44100), amplitude)
        t_lo, sig_lo = generate_sine(freq, duration, sample_rate, amplitude)

        if alias_detected:
            st.error(
                f"⚠ ALIASING — Signal {freq} Hz > Nyquist {sample_rate//2} Hz. "
                f"Alias appears at {alias_freq:.1f} Hz"
            )
        else:
            st.success(f"✓ No aliasing — {freq} Hz < Nyquist {sample_rate//2} Hz")

        fig = plot_aliasing(t_hi, sig_hi, t_lo, sig_lo,
                            alias_detected, freq, sample_rate, alias_freq)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Tab 4: Real-World Noise ───────────────────────────────────────────────
    with tabs[3]:
        st.markdown("**Real-world noise** — thermal/shot noise added before ADC quantization.")
        _, ideal = generate_sine(freq, duration, sample_rate, amplitude)
        _, noisy = generate_noisy_sine(freq, duration, sample_rate, noise_std, amplitude)
        q_noisy = quantize(noisy, bits)
        snr_noisy = compute_snr(ideal, q_noisy)
        enob_noisy = compute_enob(snr_noisy)

        c1, c2, c3 = st.columns(3)
        c1.metric("SNR (with noise)", f"{snr_noisy:.2f} dB")
        c2.metric("ENOB (with noise)", f"{enob_noisy:.2f} bits")
        c3.metric("Noise σ", f"{noise_std:.4f} V")

        metrics = {"snr": snr_noisy, "enob": enob_noisy, "noise_std": noise_std}
        fig = plot_realworld(t_s, ideal, noisy, q_noisy, metrics)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Tab 5: Dithering ─────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown("**TPDF Dithering** — two uniform RVs summed = triangular PDF. "
                    "Breaks harmonic distortion pattern, converts it to flat noise.")
        _, sig_d = generate_sine(freq, duration, sample_rate, amplitude)
        q_no_dither = quantize(sig_d, bits)
        q_dithered = quantize_with_dither(sig_d, bits)
        snr_no = compute_snr(sig_d, q_no_dither)
        snr_di = compute_snr(sig_d, q_dithered)
        thd_no = compute_thd(sig_d, q_no_dither, freq, sample_rate)
        thd_di = compute_thd(sig_d, q_dithered, freq, sample_rate)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SNR (no dither)", f"{snr_no:.1f} dB")
        c2.metric("SNR (dithered)", f"{snr_di:.1f} dB")
        c3.metric("THD (no dither)", f"{thd_no:.1f} dB")
        c4.metric("THD (dithered)", f"{thd_di:.1f} dB")

        fig = plot_dithering(t_s, sig_d, q_no_dither, q_dithered, snr_no, snr_di)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Tab 6: Spectral Analysis ──────────────────────────────────────────────
    with tabs[5]:
        st.markdown("**Spectral analysis** — FFT and PSD reveal harmonic distortion and noise floor.")
        _, sig_sp = generate_sine(freq, duration, sample_rate, amplitude)
        q_sp = quantize(sig_sp, bits)

        freqs_o, mag_o = compute_fft(sig_sp, sample_rate)
        freqs_q, mag_q = compute_fft(q_sp, sample_rate)
        freqs_po, psd_o = compute_psd(sig_sp, sample_rate)
        freqs_pq, psd_q = compute_psd(q_sp, sample_rate)

        sinad = compute_sinad(sig_sp, q_sp, sample_rate, freq)
        thd = compute_thd(sig_sp, q_sp, freq, sample_rate)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SNR", f"{compute_snr(sig_sp, q_sp):.2f} dB")
        c2.metric("SINAD", f"{sinad:.2f} dB")
        c3.metric("THD", f"{thd:.2f} dB")
        c4.metric("ENOB (SINAD)", f"{compute_enob(sinad):.2f} bits")

        fig_fft = plot_fft_spectrum(freqs_o, mag_o, freqs_q, mag_q, freq, sample_rate)
        st.plotly_chart(fig_fft, use_container_width=True, config=PLOTLY_CONFIG)

        fig_psd = plot_psd(freqs_po, psd_o, freqs_pq, psd_q,
                           bits=bits, sample_rate=sample_rate)
        st.plotly_chart(fig_psd, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Tab 7: Advanced Characterization ─────────────────────────────────────
    with tabs[6]:
        st.markdown(
            "**Advanced** — DNL/INL, ENOB vs frequency (aperture jitter), "
            "and waveform type comparison."
        )

        sub1, sub2 = st.tabs(["DNL / INL", "ENOB vs Frequency"])

        with sub1:
            # Use a slow ramp for DNL accuracy
            t_ramp = np.linspace(-0.99, 0.99, 8192)
            q_ramp = quantize(t_ramp, bits)
            dnl = compute_dnl(t_ramp, bits)
            inl = compute_inl(dnl)

            c1, c2 = st.columns(2)
            c1.metric("Max |DNL|", f"{float(np.max(np.abs(dnl))):.3f} LSB")
            c2.metric("Max |INL|", f"{float(np.max(np.abs(inl))):.3f} LSB")

            import plotly.graph_objects as go
            codes = list(range(len(dnl)))

            fig_dnl = go.Figure()
            fig_dnl.add_trace(go.Bar(x=codes, y=dnl.tolist(),
                                     name="DNL",
                                     marker_color="#378ADD", opacity=0.8))
            fig_dnl.add_hline(y=0, line_color="#555", line_width=0.8)
            fig_dnl.add_hline(y=1, line_color="#E24B4A", line_width=1,
                              line_dash="dash",
                              annotation_text="+1 LSB (missing code threshold)",
                              annotation_font_size=10)
            fig_dnl.add_hline(y=-1, line_color="#E24B4A", line_width=1,
                              line_dash="dash")
            fig_dnl.update_layout(
                height=320,
                title="Differential Non-Linearity (DNL) per code",
                xaxis_title="Code", yaxis_title="DNL (LSB)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", size=11),
                margin=dict(l=60, r=30, t=45, b=50),
            )
            st.plotly_chart(fig_dnl, use_container_width=True, config=PLOTLY_CONFIG)

            fig_inl = go.Figure()
            fig_inl.add_trace(go.Scatter(x=codes, y=inl.tolist(),
                                         mode="lines", name="INL",
                                         line=dict(color="#D85A30", width=1.5)))
            fig_inl.update_layout(
                height=300,
                title="Integral Non-Linearity (INL) per code",
                xaxis_title="Code", yaxis_title="INL (LSB)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", size=11),
                margin=dict(l=60, r=30, t=45, b=50),
            )
            st.plotly_chart(fig_inl, use_container_width=True, config=PLOTLY_CONFIG)

        with sub2:
            jitter_ps = st.slider("Aperture jitter (ps RMS)", 0, 500, 10)
            jitter_s = jitter_ps * 1e-12
            freq_range = np.logspace(2, np.log10(sample_rate / 2), 200)
            enob_arr = compute_enob_vs_frequency(bits, jitter_s, freq_range)

            import plotly.graph_objects as go
            fig_enob = go.Figure()
            fig_enob.add_trace(go.Scatter(
                x=freq_range.tolist(), y=enob_arr.tolist(),
                mode="lines", name=f"ENOB ({jitter_ps} ps jitter)",
                line=dict(color="#378ADD", width=2),
            ))
            fig_enob.add_hline(y=bits, line_color="#1D9E75", line_width=1,
                               line_dash="dash",
                               annotation_text=f"Ideal {bits}-bit ENOB",
                               annotation_font_size=10)
            fig_enob.update_layout(
                height=380,
                title="ENOB vs Input Frequency (aperture jitter degradation)",
                xaxis=dict(title="Input frequency (Hz)", type="log",
                           gridcolor="rgba(128,128,128,0.18)"),
                yaxis=dict(title="ENOB (bits)", gridcolor="rgba(128,128,128,0.18)"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", size=11),
                margin=dict(l=60, r=30, t=45, b=50),
            )
            st.plotly_chart(fig_enob, use_container_width=True, config=PLOTLY_CONFIG)


# ─────────────────────────────────────────────────────────────────────────────
# QUANTUM READOUT
# ─────────────────────────────────────────────────────────────────────────────
def show_quantum_ui():
    import plotly.graph_objects as go

    st.markdown('<div style="padding:20px 28px 0">', unsafe_allow_html=True)
    st.markdown("""
<div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.1em;
     text-transform:uppercase;color:var(--c-purple,#6c3fc1);margin-bottom:6px">
  Quantum Readout Analysis
</div>
<div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;
     color:var(--c-text);letter-spacing:-.03em;margin-bottom:4px">
  ADC Resolution → Qubit Fidelity
</div>
<div style="font-family:'DM Sans',sans-serif;font-size:13px;color:var(--c-text2);
     line-height:1.6;margin-bottom:16px">
  IQ scatter, shot noise, erfc readout model, Standard Quantum Limit,
  T1/T2 context, and Qiskit circuit simulation.
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Qiskit status banner ──────────────────────────────────────────────────
    qstatus = qr.get_status()
    if qstatus["mode"] == "full":
        st.success("⚛️ Qiskit + AerSimulator available — running real circuit simulations")
    elif qstatus["mode"] == "qiskit_only":
        st.info("⚛️ Qiskit available (no Aer) — using statevector simulation")
    else:
        st.info(
            "⚛️ Qiskit not installed — using statistical fallback model. "
            "Add `qiskit` and `qiskit-aer` to requirements.txt to enable full simulation."
        )

    # ── Sidebar controls ──────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Quantum Controls")
        q_bits     = st.slider("ADC bit depth", 4, 16, 12)
        q_freq     = st.slider("Readout frequency (MHz)", 1, 500, 50)
        q_duration = st.slider("Readout duration (μs)", 1, 10, 2)
        n_photons  = st.slider("Photon number (N)", 1, 1000, 100)
        noise_std_q = st.slider("IQ noise σ", 0.01, 0.2, 0.05, 0.005)
        n_shots    = st.slider("Qiskit shots", 100, 2000, 500, 100)

    # ── Signal physics ────────────────────────────────────────────────────────
    freq_hz = q_freq * 1e6
    dur_s   = q_duration * 1e-6
    sr      = min(int(freq_hz * 10), 500_000)

    t_q, pulse = generate_sine(freq_hz, dur_s, sr, amplitude=0.8)
    q_pulse    = quantize(pulse, q_bits)
    noise_floor_v = 2.0 / (2 ** q_bits)

    adc_snr      = compute_snr(pulse, q_pulse)
    shot_snr     = compute_shot_noise_snr(n_photons)
    total_snr    = combined_readout_snr(adc_snr, n_photons)
    readout_error = snr_to_readout_error(total_snr)
    fidelity     = 1.0 - readout_error

    I_0, Q_0, I_1, Q_1 = generate_iq_signal(
        freq_hz, dur_s, sr,
        amplitude_0=0.3, amplitude_1=0.7,
        noise_std=noise_std_q, n_shots=n_shots,
    )

    # ── Metrics row ───────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ADC SNR",         f"{adc_snr:.1f} dB")
    c2.metric("Shot-noise SNR",  f"{shot_snr:.1f} dB")
    c3.metric("Total SNR",       f"{total_snr:.1f} dB")
    c4.metric("Readout error",   f"{readout_error*100:.3f}%")
    c5.metric("Fidelity",        f"{fidelity*100:.2f}%")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "⚛️ Readout Circuit",
        "🔔 Bell State",
        "🔍 Grover Search",
        "📉 T1 Decay",
        "📊 Fidelity Sweep",
        "📖 Physics Notes",
    ])

    # ── Tab 1 — Readout Circuit ───────────────────────────────────────────────
    with tabs[0]:
        counts = qr.run_readout_circuit(fidelity, shots=n_shots)

        # Main quantum IQ + pulse plot
        fig = plot_quantum(t_q, q_pulse, noise_floor_v, q_bits,
                           readout_error, counts, I_0, Q_0, I_1, Q_1)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        col_circ, col_hist = st.columns([1, 1])

        with col_circ:
            st.markdown("**Circuit diagram**")
            st.code(qr.get_circuit_diagram("readout", fidelity=fidelity), language=None)
            st.caption(
                "H gate puts qubit in |+⟩ superposition. "
                "RX(ε) models readout error angle. Measurement collapses to |0⟩ or |1⟩."
            )

        with col_hist:
            st.markdown("**Measurement histogram**")
            labels = sorted(counts.keys())
            vals   = [counts.get(k, 0) for k in labels]
            total  = sum(vals) or 1
            fig_hist = go.Figure(go.Bar(
                x=labels, y=vals,
                marker_color=["#6c3fc1" if l == "1" else "#14a3a8" for l in labels],
                text=[f"{v}<br>{v/total*100:.1f}%" for v in vals],
                textposition="outside",
            ))
            fig_hist.update_layout(
                height=300, title=f"Readout counts (shots={n_shots})",
                xaxis_title="Measurement outcome",
                yaxis_title="Count",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", size=11),
                margin=dict(l=50, r=30, t=45, b=50),
                showlegend=False,
            )
            st.plotly_chart(fig_hist, use_container_width=True, config=PLOTLY_CONFIG)

    # ── Tab 2 — Bell State ────────────────────────────────────────────────────
    with tabs[1]:
        bell_counts = qr.run_bell_circuit(shots=n_shots)

        col_b1, col_b2 = st.columns([1, 1])

        with col_b1:
            st.markdown("**Bell circuit |Φ+⟩ = (|00⟩ + |11⟩)/√2**")
            st.code(qr.get_circuit_diagram("bell"), language=None)
            st.caption(
                "H gate on q0 creates superposition. CNOT entangles q0→q1. "
                "Perfect Bell state shows only |00⟩ and |11⟩ outcomes."
            )

        with col_b2:
            st.markdown("**Bell measurement histogram**")
            labels_b = sorted(bell_counts.keys())
            vals_b   = [bell_counts.get(k, 0) for k in labels_b]
            total_b  = sum(vals_b) or 1
            colors_b = {"00": "#14a3a8", "01": "#c17d11", "10": "#c17d11", "11": "#6c3fc1"}
            fig_bell = go.Figure(go.Bar(
                x=labels_b, y=vals_b,
                marker_color=[colors_b.get(l, "#888") for l in labels_b],
                text=[f"{v}<br>{v/total_b*100:.1f}%" for v in vals_b],
                textposition="outside",
            ))
            fig_bell.update_layout(
                height=300, title=f"Bell state counts (shots={n_shots})",
                xaxis_title="Measurement outcome",
                yaxis_title="Count",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", size=11),
                margin=dict(l=50, r=30, t=45, b=50),
                showlegend=False,
            )
            st.plotly_chart(fig_bell, use_container_width=True, config=PLOTLY_CONFIG)

        # Entanglement quality metric
        p00 = bell_counts.get("00", 0) / total_b
        p11 = bell_counts.get("11", 0) / total_b
        p_entangled = p00 + p11
        concurrence_est = max(0.0, 2 * p_entangled - 1.0)
        st.markdown("**Entanglement quality**")
        m1, m2, m3 = st.columns(3)
        m1.metric("P(|00⟩) + P(|11⟩)", f"{p_entangled*100:.1f}%",
                  help="Should be ~100% for ideal Bell state")
        m2.metric("Estimated concurrence", f"{concurrence_est:.3f}",
                  help="1.0 = maximally entangled, 0 = separable")
        m3.metric("Crosstalk leakage", f"{(1-p_entangled)*100:.1f}%",
                  help="|01⟩ + |10⟩ outcomes — indicates readout crosstalk")

    # ── Tab 3 — Grover Search ─────────────────────────────────────────────────
    with tabs[2]:
        grover_counts = qr.run_grover_circuit(shots=n_shots)

        col_g1, col_g2 = st.columns([1, 1])

        with col_g1:
            st.markdown("**2-qubit Grover — oracle marks |11⟩**")
            st.code(qr.get_circuit_diagram("grover"), language=None)
            st.caption(
                "H⊗2 creates uniform superposition. CZ oracle flips phase of |11⟩. "
                "Diffuser amplifies |11⟩ probability. 1 iteration → ~75% success."
            )

        with col_g2:
            st.markdown("**Grover measurement histogram**")
            labels_g = sorted(grover_counts.keys())
            vals_g   = [grover_counts.get(k, 0) for k in labels_g]
            total_g  = sum(vals_g) or 1
            colors_g = {"11": "#6c3fc1"}
            fig_grov = go.Figure(go.Bar(
                x=labels_g, y=vals_g,
                marker_color=[colors_g.get(l, "#888888") for l in labels_g],
                text=[f"{v}<br>{v/total_g*100:.1f}%" for v in vals_g],
                textposition="outside",
            ))
            fig_grov.update_layout(
                height=300, title=f"Grover counts (shots={n_shots})",
                xaxis_title="Measurement outcome",
                yaxis_title="Count",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", size=11),
                margin=dict(l=50, r=30, t=45, b=50),
                showlegend=False,
            )
            st.plotly_chart(fig_grov, use_container_width=True, config=PLOTLY_CONFIG)

        p_marked = grover_counts.get("11", 0) / total_g
        st.metric("P(|11⟩) — target state", f"{p_marked*100:.1f}%",
                  delta=f"{(p_marked - 0.25)*100:+.1f}% vs random 25%",
                  help="Ideal Grover gives ~75% after 1 iteration on 2-qubit space")

    # ── Tab 4 — T1 Decay ─────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("""
**T1 relaxation** — qubit starts in |1⟩ (X gate), then decays over time.
P(|1⟩) = exp(−t/T₁). Each delay step = one identity gate (one clock cycle).
        """)

        t1_steps_max = st.slider("T1 characteristic steps", 5, 50, 20, key="t1_char")
        delay_steps  = st.slider("Probe delay (steps)", 0, t1_steps_max, 0, key="t1_delay")

        # Single shot at chosen delay
        t1_counts = qr.run_t1_circuit(delay_steps, shots=n_shots, t1_steps=t1_steps_max)

        # Full sweep
        steps_arr, p1_arr = qr.compute_t1_sweep(shots=n_shots, max_steps=t1_steps_max)
        t_fit = np.linspace(0, t1_steps_max, 200)
        p_fit = np.exp(-t_fit / max(t1_steps_max, 1))

        fig_t1 = go.Figure()
        fig_t1.add_trace(go.Scatter(
            x=steps_arr.tolist(), y=p1_arr.tolist(),
            mode="markers+lines", name="P(|1⟩) measured",
            marker=dict(size=7, color="#6c3fc1"),
            line=dict(color="#6c3fc1", width=1.5),
            hovertemplate="delay=%{x} steps<br>P(|1⟩)=%{y:.3f}<extra></extra>",
        ))
        fig_t1.add_trace(go.Scatter(
            x=t_fit.tolist(), y=p_fit.tolist(),
            mode="lines", name="Ideal exp(−t/T₁)",
            line=dict(color="#14a3a8", width=1.5, dash="dash"),
        ))
        fig_t1.add_vline(x=delay_steps, line_color="#c17d11", line_dash="dot",
                         annotation_text=f"probe = {delay_steps}", annotation_font_size=10)
        fig_t1.update_layout(
            height=360, title="T1 Decay: P(|1⟩) vs delay",
            xaxis=dict(title="Delay (identity gate steps)", gridcolor="rgba(128,128,128,0.18)"),
            yaxis=dict(title="P(|1⟩)", range=[0, 1.05], gridcolor="rgba(128,128,128,0.18)"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", size=11),
            margin=dict(l=60, r=30, t=45, b=50),
            showlegend=True,
        )
        st.plotly_chart(fig_t1, use_container_width=True, config=PLOTLY_CONFIG)

        total_t1 = sum(t1_counts.values()) or 1
        p1_probe = t1_counts.get("1", 0) / total_t1
        st.code(qr.get_circuit_diagram("t1", delay_steps=delay_steps), language=None)
        st.metric(f"P(|1⟩) at delay={delay_steps}", f"{p1_probe*100:.1f}%",
                  help="Exponential decay from 100% at delay=0")

    # ── Tab 5 — Fidelity Sweep ────────────────────────────────────────────────
    with tabs[4]:
        bits_arr = list(range(4, 17))
        errors, fidelities = [], []
        for b in bits_arr:
            _, p = generate_sine(freq_hz, dur_s, sr, amplitude=0.8)
            q   = quantize(p, b)
            s   = compute_snr(p, q)
            tot = combined_readout_snr(s, n_photons)
            err = snr_to_readout_error(tot)
            errors.append(err * 100)
            fidelities.append((1.0 - err) * 100)

        from plotly.subplots import make_subplots as _ms
        fig_sw = _ms(rows=2, cols=1, shared_xaxes=True,
                     subplot_titles=["Readout error (%) vs ADC bit depth",
                                     "Fidelity (%) vs ADC bit depth"],
                     vertical_spacing=0.14)
        fig_sw.add_trace(go.Scatter(
            x=bits_arr, y=errors, mode="lines+markers",
            line=dict(color="#E24B4A", width=2), marker=dict(size=6),
            name="Readout error",
            hovertemplate="<b>%{x} bits</b><br>Error=%{y:.4f}%<extra></extra>",
        ), row=1, col=1)
        fig_sw.add_hline(y=1.0, row=1, col=1, line_dash="dash",
                         line_color="#E24B4A",
                         annotation_text="1% threshold", annotation_font_size=10)

        fig_sw.add_trace(go.Scatter(
            x=bits_arr, y=fidelities, mode="lines+markers",
            line=dict(color="#6c3fc1", width=2), marker=dict(size=6),
            name="Fidelity",
            hovertemplate="<b>%{x} bits</b><br>Fidelity=%{y:.4f}%<extra></extra>",
        ), row=2, col=1)
        fig_sw.add_hline(y=99.0, row=2, col=1, line_dash="dash",
                         line_color="#1D9E75",
                         annotation_text="IBM 99% target", annotation_font_size=10)

        fig_sw.update_xaxes(title_text="ADC Bit Depth", tickmode="linear",
                            tick0=4, dtick=1, row=2, col=1,
                            gridcolor="rgba(128,128,128,0.18)")
        fig_sw.update_yaxes(gridcolor="rgba(128,128,128,0.18)")
        fig_sw.update_layout(
            height=520,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", size=11),
            margin=dict(l=60, r=30, t=55, b=50),
            showlegend=False,
        )
        st.plotly_chart(fig_sw, use_container_width=True, config=PLOTLY_CONFIG)

        # SQL line annotation
        sql_bits = next((b for b, e in zip(bits_arr, errors) if e < 0.01), None)
        if sql_bits:
            st.info(
                f"📐 **Standard Quantum Limit reached at ~{sql_bits} bits** — "
                f"beyond this, shot noise dominates and more ADC bits give no fidelity gain."
            )

    # ── Tab 6 — Physics Notes ─────────────────────────────────────────────────
    with tabs[5]:
        st.markdown("""
### Readout error model (Krantz et al. 2019, eq. 22)
```
error = 0.5 × erfc(√(SNR_total / 2))
```

### Combined SNR (ADC noise + shot noise)
```
1/SNR_total = 1/SNR_adc + 1/SNR_shot
SNR_shot    = 5·log₁₀(N_photons)  dB
```

### Standard Quantum Limit
Beyond ~14 bits ADC, shot noise dominates → more bits give zero fidelity improvement.
This is the SQL for dispersive readout in superconducting qubit architectures.

### IBM target
> 99% assignment fidelity requires ≥ 12-bit ADC at ~1 GHz sample rate.

### Qiskit circuits used
| Circuit | Gates | Purpose |
|---------|-------|---------|
| Readout | H, RX(ε), M | Models single-qubit dispersive readout with fidelity-linked error |
| Bell state | H, CNOT, M×2 | Entanglement verification — only \\|00⟩ and \\|11⟩ should appear |
| Grover 2-qubit | H⊗2, CZ, diffuser, M×2 | Amplitude amplification — marks \\|11⟩, ~75% probability |
| T1 decay | X, id×N, M | Longitudinal relaxation — P(\\|1⟩) decays as exp(−t/T₁) |

### References
- Krantz et al., *A Quantum Engineer's Guide to Superconducting Qubits*, Appl. Phys. Rev. 6, 2019
- IBM Quantum, *Quantum Volume and Readout Fidelity*, 2022
- IEEE Std 1241-2010, *ADC Testing Standard*
        """)


def show_comparison_ui():
    st.markdown('<div style="padding:20px 28px 0">', unsafe_allow_html=True)
    st.markdown("""
<div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.1em;
     text-transform:uppercase;color:var(--c-amber,#c17d11);margin-bottom:6px">
  Comparison Mode
</div>
<div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;
     color:var(--c-text);letter-spacing:-.03em;margin-bottom:4px">
  Side-by-Side ADC Performance
</div>
<div style="font-family:'DM Sans',sans-serif;font-size:13px;color:var(--c-text2);
     line-height:1.6;margin-bottom:16px">
  Compare bit depths and oversampling factors side-by-side.
  Instantly see the quality delta across time domain and FFT.
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    compare_mode = st.radio(
        "Comparison type",
        ["Bit depth", "Oversampling factor"],
        horizontal=True,
    )

    with st.sidebar:
        st.markdown("### Comparison Controls")
        freq_c = st.slider("Signal frequency (Hz)", 10, 5000, 440)
        sr_c = st.select_slider(
            "Sample rate (Hz)",
            options=[1000, 2000, 4000, 8000, 16000, 44100, 48000],
            value=8000,
        )
        amp_c = st.slider("Amplitude", 0.1, 1.0, 0.9, 0.05)
        dur_c = st.slider("Duration (s)", 0.01, 0.5, 0.05, 0.01)

    t_c, sig_c = generate_sine(freq_c, dur_c, sr_c, amp_c)

    if compare_mode == "Bit depth":
        bits_lo = st.select_slider("Low bit depth", options=list(range(1, 17)), value=4)
        bits_hi = st.select_slider("High bit depth", options=list(range(1, 17)), value=16)

        q_lo = quantize(sig_c, bits_lo)
        q_hi = quantize(sig_c, bits_hi)

        snr_lo = compute_snr(sig_c, q_lo)
        snr_hi = compute_snr(sig_c, q_hi)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"SNR ({bits_lo}-bit)", f"{snr_lo:.1f} dB")
        c2.metric(f"SNR ({bits_hi}-bit)", f"{snr_hi:.1f} dB")
        c3.metric("SNR Δ", f"+{snr_hi - snr_lo:.1f} dB")
        c4.metric("ENOB Δ", f"+{compute_enob(snr_hi) - compute_enob(snr_lo):.2f} bits")

        signals = {
            "Original": sig_c,
            f"{bits_lo}-bit ADC": q_lo,
            f"{bits_hi}-bit ADC": q_hi,
        }
        fig = plot_comparison(t_c, signals, mode="bit_depth")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        with st.expander("FFT comparison"):
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots as ms

            freqs_lo, mag_lo = compute_fft(q_lo, sr_c)
            freqs_hi, mag_hi = compute_fft(q_hi, sr_c)

            fig_f = ms(rows=2, cols=1, shared_xaxes=True,
                       subplot_titles=[f"{bits_lo}-bit FFT", f"{bits_hi}-bit FFT"],
                       vertical_spacing=0.12)
            fig_f.add_trace(go.Scatter(x=freqs_lo, y=mag_lo, mode="lines",
                                       line=dict(color="#D85A30", width=1.2),
                                       name=f"{bits_lo}-bit"), row=1, col=1)
            fig_f.add_trace(go.Scatter(x=freqs_hi, y=mag_hi, mode="lines",
                                       line=dict(color="#378ADD", width=1.2),
                                       name=f"{bits_hi}-bit"), row=2, col=1)
            fig_f.update_layout(height=520,
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(family="monospace", size=11),
                                margin=dict(l=65, r=45, t=55, b=65))
            fig_f.update_xaxes(title_text="Frequency (Hz)", row=2, col=1)
            fig_f.update_yaxes(title_text="Magnitude (dBFS)", row=1, col=1)
            fig_f.update_yaxes(title_text="Magnitude (dBFS)", row=2, col=1)
            st.plotly_chart(fig_f, use_container_width=True, config=PLOTLY_CONFIG)

    else:  # Oversampling comparison
        bits_ov = st.select_slider("Bit depth", options=list(range(1, 17)), value=8)
        osr_lo = 1
        osr_hi = st.select_slider("High oversample factor",
                                   options=[2, 4, 8, 16, 32, 64], value=64)

        # 1× — no oversampling
        q_1x = quantize(sig_c, bits_ov)
        snr_1x = compute_snr(sig_c, q_1x)

        # Nx — oversample → quantize → decimate
        t_hi2, sig_hi2 = generate_sine(freq_c, dur_c, sr_c * osr_hi, amp_c)
        over_sig2, actual_osr = oversample(sig_hi2, osr_hi)
        q_over2 = quantize(over_sig2, bits_ov)
        dec2 = downsample_quantized(q_over2, actual_osr)

        min_len = min(len(sig_c), len(dec2))
        snr_nx = compute_snr(sig_c[:min_len], dec2[:min_len])
        exp_gain = 10 * np.log10(actual_osr) / 2

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SNR (1×)", f"{snr_1x:.1f} dB")
        c2.metric(f"SNR ({actual_osr}×)", f"{snr_nx:.1f} dB")
        c3.metric("Actual gain", f"+{snr_nx - snr_1x:.1f} dB")
        c4.metric("Theory gain", f"+{exp_gain:.1f} dB")

        signals_osr = {
            "Original": sig_c[:min_len],
            f"1× (no OSR)": q_1x[:min_len],
            f"{actual_osr}× oversampled": dec2[:min_len],
        }
        fig = plot_comparison(t_c[:min_len], signals_osr, mode="oversampling")
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

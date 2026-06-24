l        "format": "json",
        "COMMAND": str(target),
        "EPHEM_TYPE": "VECTORS",
        "CENTER": "500",
        "START_TIME": start_time,
        "STOP_TIME": stop_time,
        "STEP_SIZE": step,
    }
    resp = requests.get(HORIZONS_API, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    text = data.get("result") if isinstance(data, dict) else resp.text
    return parse_horizons_result(text)


def parse_horizons_result(text: str) -> pd.DataFrame:
    # extract block between $$SOE and $$EOE
    m = re.search(r"\$\$SOE(.*?)\$\$EOE", text, re.S)
    block = m.group(1).strip() if m else text
    lines = [l.strip() for l in block.splitlines() if l.strip()]

    rows = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # look for JD/time lines that start with a number
        if re.match(r"^\d+\.\d+", line):
            # parse calendar date if present
            dt = None
            dt_match = re.search(r"(\d{4}-[A-Za-z]{3}-\d{2} \d{2}:\d{2}:\d{2})", line)
            if dt_match:
                try:
                    dt = datetime.strptime(dt_match.group(1), "%Y-%b-%d %H:%M:%S")
                except Exception:
                    dt = None

            # next line: X Y Z
            x = y = z = None
            if i + 1 < len(lines):
                vals = re.findall(r"[-+]?[0-9]*\.?[0-9]+E[-+]?[0-9]+|[-+]?[0-9]*\.?[0-9]+", lines[i + 1])
                if len(vals) >= 3:
                    x, y, z = map(float, vals[:3])

            # following line: VX VY VZ (may include other numbers after)
            vx = vy = vz = None
            if i + 2 < len(lines):
                vals2 = re.findall(r"[-+]?[0-9]*\.?[0-9]+E[-+]?[0-9]+|[-+]?[0-9]*\.?[0-9]+", lines[i + 2])
                if len(vals2) >= 3:
                    vx, vy, vz = map(float, vals2[:3])

            rows.append({"time": dt, "x": x, "y": y, "z": z, "vx": vx, "vy": vy, "vz": vz})
            i += 3
        else:
            i += 1

    return pd.DataFrame(rows)


def plot_vectors(df: pd.DataFrame, title="Ephemeris"):
    fig = go.Figure()
    # Earth at origin
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[0], mode="markers", marker=dict(size=6, color="blue"), name="Earth"))
    if not df.empty:
        fig.add_trace(
            go.Scatter3d(
                x=df["x"],
                y=df["y"],
                z=df["z"],
                mode="lines+markers",
                marker=dict(size=3, color="red"),
                name="Target",
            )
        )
    fig.update_layout(title=title, scene=dict(xaxis_title="X (km)", yaxis_title="Y (km)", zaxis_title="Z (km)"))
    return fig


def main():
    st.title("AROW - Live Simulator Prototype")

    col1, col2 = st.columns([2, 1])
    with col1:
        target = st.text_input("Horizons target (ID or name)", value="301")
        start_date = st.date_input("Start date", value=datetime.utcnow().date())
        duration_days = st.number_input("Duration (days)", min_value=0.00069444, value=1.0, format="%.6f")
        step = st.text_input("Step size (e.g. 1h, 1m)", value="1h")

    with col2:
        poll = st.number_input("Poll interval (s)", min_value=10, value=60, step=10)
        st.write("Data source: JPL Horizons")

    start = datetime.combine(start_date, datetime.min.time())
    stop = start + timedelta(days=float(duration_days))

    if st.button("Fetch now"):
        with st.spinner("Querying JPL Horizons..."):
            try:
                df = fetch_horizons_vectors(target, start.strftime("%Y-%m-%d"), stop.strftime("%Y-%m-%d"), step=step)
                if df.empty:
                    st.error("No ephemeris rows parsed from Horizons response.")
                    return
                st.success(f"Fetched {len(df)} rows")
                st.dataframe(df.drop(columns=[c for c in df.columns if c not in ["time", "x", "y", "z"]]).head(20))
                fig = plot_vectors(df, title=f"Target {target}")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Query failed: {e}")


if __name__ == "__main__":
    main()

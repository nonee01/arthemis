import math
import argparse

# --- MISSION CONSTANTS ---
EARTH_RADIUS = 6371
MOON_RADIUS = 1737
# Placing the Moon slightly inward on the X-axis so our path wraps behind it
MOON_X = 375000
MOON_Y = 0
MISSION_DAYS = 10
FLYBY_ALTITUDE = 9400  # Defines how far past the moon center the ship travels

# Display scale used when drawing the Moon (keeps visuals large enough)
MOON_DISPLAY_SCALE = 3

# Default animation parameters
FRAMES_COUNT = 600


def check_los(x_sc, y_sc, moon_x=None, moon_y=None, moon_radius=None, moon_display_scale=None):
    """
    Checks if the Moon is blocking the line of sight from Earth (0,0) to Spacecraft.
    Uses point-to-line geometry. Optional parameters allow testing with different
    Moon positions/sizes without mutating module-level constants.
    """
    if moon_x is None:
        moon_x = MOON_X
    if moon_y is None:
        moon_y = MOON_Y
    if moon_radius is None:
        moon_radius = MOON_RADIUS
    if moon_display_scale is None:
        moon_display_scale = MOON_DISPLAY_SCALE

    if x_sc == 0 and y_sc == 0:
        return False

    # Distance from Moon center to the signal line (y_sc * X - x_sc * Y = 0)
    dist_to_line = abs(y_sc * moon_x) / math.sqrt(x_sc**2 + y_sc**2)

    # LOS occurs if the signal line passes through the Moon AND spacecraft is behind it
    if dist_to_line < (moon_radius * moon_display_scale) and x_sc > moon_x:
        return True
    return False


def run_simulation(moon_x=MOON_X, moon_y=MOON_Y, mission_days=MISSION_DAYS,
                   flyby_altitude=FLYBY_ALTITUDE, frames_count=FRAMES_COUNT,
                   headless=False):
    """Create and run the Matplotlib animation. Kept separate so module import
    does not start GUI operations (useful for tests and headless runs).
    """
    # Import plotting libraries lazily so module import doesn't require them
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation

    # --- SETUP THE VISUAL DASHBOARD ---
    fig, ax = plt.subplots(figsize=(12, 7))
    try:
        fig.canvas.manager.set_window_title('Artemis 2 Mission Control')
    except Exception:
        # Some backends (or headless environments) may not support window titles
        pass

    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    ax.set_aspect('equal')

    # Set view area (zoomed out to see Earth and Moon)
    ax.set_xlim(-50000, moon_x + 45000)
    ax.set_ylim(-150000, 150000)
    ax.axis('off')

    # Draw Celestial Bodies (Sizes slightly exaggerated for screen visibility)
    earth = plt.Circle((0, 0), EARTH_RADIUS * 2, color='royalblue', zorder=5)
    moon = plt.Circle((moon_x, moon_y), MOON_RADIUS * MOON_DISPLAY_SCALE, color='lightgray', zorder=5)
    ax.add_patch(earth)
    ax.add_patch(moon)

    # Labels for bodies (store references for path effects)
    earth_label = ax.text(-20000, -20000, 'EARTH', color='royalblue', fontweight='bold')
    moon_label = ax.text(moon_x - 10000, -20000, 'MOON', color='lightgray', fontweight='bold')

    # Initialize moving elements
    trajectory_line, = ax.plot([], [], color='gray', linestyle='--', alpha=0.4)
    spacecraft, = ax.plot([], [], 'o', color='orange', markersize=8, zorder=10)
    signal_line, = ax.plot([], [], color='cyan', linewidth=1.5, zorder=4, alpha=0.8)

    # Initialize Telemetry UI
    # `status_text` removed to avoid overlapping telemetry; use `comm_text` instead
    comm_text = ax.text(0.99, 0.98, '', transform=ax.transAxes, ha='right', va='top', color='cyan', fontsize=14, fontweight='bold', fontfamily='monospace')
    watermark_text = ax.text(0.01, 0.01, 'made by Yassine El Aidous', transform=ax.transAxes, ha='left', va='bottom', color='white', fontsize=9, alpha=0.75)

    # --- CALCULATE THE TRAJECTORY ---
    # Import NumPy lazily to avoid requiring it at module import time
    import numpy as np

    # We use parametric equations to generate the classic "Figure-8" free-return path
    t = np.linspace(0, mission_days, frames_count)

    # X-axis expands out to the Moon and back
    x_traj = (moon_x + flyby_altitude) * np.sin(np.pi * t / mission_days)
    # Y-axis creates the loop (crosses zero twice to make the 8 shape)
    y_traj = 120000 * np.sin(2 * np.pi * t / mission_days)

    # Draw the planned path in the background
    trajectory_line.set_data(x_traj, y_traj)

    # --- STARFIELD BACKGROUND ---
    from matplotlib.collections import LineCollection
    import matplotlib.patheffects as pe
    from matplotlib import cm, colors as mcolors

    # Starfield (reproducible)
    rng = np.random.RandomState(42)
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    n_stars = 450
    star_x = rng.uniform(xmin, xmax, n_stars)
    star_y = rng.uniform(ymin, ymax, n_stars)
    star_sizes = rng.uniform(6, 30, n_stars) * 0.2
    star_alphas = rng.uniform(0.06, 0.9, n_stars)
    star_colors = np.ones((n_stars, 4))
    star_colors[:, 3] = star_alphas
    star_scatter = ax.scatter(star_x, star_y, s=star_sizes, facecolors=star_colors, edgecolors='none', zorder=0)

    # Path effects for text for better legibility
    pe_stroke = [pe.withStroke(linewidth=3, foreground='black')]
    for txt in (comm_text, earth_label, moon_label, watermark_text):
        txt.set_path_effects(pe_stroke)

    # --- ENHANCED VISUALS & KINEMATICS ---
    # Precompute derivatives and LOS array for prediction/telemetry
    vx_day = np.gradient(x_traj, t)  # km per day
    vy_day = np.gradient(y_traj, t)
    speed_day = np.sqrt(vx_day ** 2 + vy_day ** 2)
    speed_s = speed_day / 86400.0  # convert to km/s

    # velocity components in km/s and heading
    vx_s = vx_day / 86400.0
    vy_s = vy_day / 86400.0
    heading_deg = np.degrees(np.arctan2(vy_s, vx_s))

    r = np.sqrt(x_traj ** 2 + y_traj ** 2)
    radial_day = (x_traj * vx_day + y_traj * vy_day) / np.maximum(r, 1e-9)
    radial_s = radial_day / 86400.0

    # specific orbital energy relative to Earth (km^2/s^2)
    MU_EARTH = 398600.4418
    energy = 0.5 * (speed_s ** 2) - MU_EARTH / np.maximum(r, 1e-9)
    # approximate semi-major axis when bound
    a_arr = np.where(energy < 0, -MU_EARTH / (2.0 * energy), np.nan)

    los_array = np.array([
        check_los(x_traj[i], y_traj[i], moon_x=moon_x, moon_y=moon_y,
                  moon_radius=MOON_RADIUS, moon_display_scale=MOON_DISPLAY_SCALE)
        for i in range(frames_count)
    ])

    # Distance to Moon for closest-approach predictions
    dist_moon_arr = np.sqrt((x_traj - moon_x) ** 2 + (y_traj - moon_y) ** 2)

    # Trail settings (fading) - use LineCollection for smooth gradient trail
    trail_len = min(160, max(20, frames_count // 4))
    from matplotlib.collections import LineCollection

    norm = mcolors.Normalize(vmin=speed_s.min(), vmax=speed_s.max())
    cmap = plt.get_cmap('plasma')
    trail_lc = LineCollection([], linewidths=2.8, zorder=8, capstyle='round')
    ax.add_collection(trail_lc)

    # Spacecraft halo (soft glow)
    spacecraft_halo = plt.Circle((0, 0), 22000, color='orange', alpha=0.12, zorder=7)
    ax.add_patch(spacecraft_halo)

    # Telemetry block (more detailed)
    telemetry_text = ax.text(-40000, 80000, '', color='white', fontsize=11, fontfamily='monospace')
    # Apply path effects to telemetry_text as well (created after pe_stroke)
    telemetry_text.set_path_effects(pe_stroke)

    # Compute full path length for summary
    path_length = np.sum(np.sqrt(np.diff(x_traj) ** 2 + np.diff(y_traj) ** 2))

    # --- ANIMATION LOOP ---
    def animate(frame):
        # Get current position
        x = x_traj[frame]
        y = y_traj[frame]
        current_t = t[frame]

        # Update Orion position
        spacecraft.set_data([x], [y])

        # Run communications check
        is_los = bool(los_array[frame])

        if is_los:
            msg = 'COMM: [ LOSS OF SIGNAL - FAR SIDE ]'
            signal_line.set_data([], [])  # Turn off laser signal
            comm_text.set_text(msg)
            comm_text.set_color('red')
            spacecraft.set_color('red')
            moon.set_facecolor((0.5, 0.1, 0.1))
            moon.set_alpha(0.9)
        else:
            msg = 'COMM: [ ACQUISITION OF SIGNAL ]'
            signal_line.set_data([0, x], [0, y])  # Draw laser from Earth to Orion
            comm_text.set_text(msg)
            comm_text.set_color('cyan')
            spacecraft.set_color('orange')
            moon.set_facecolor('lightgray')
            moon.set_alpha(1.0)

        # Update gradient trail using LineCollection
        start = max(0, frame - trail_len + 1)
        xs = x_traj[start:frame + 1]
        ys = y_traj[start:frame + 1]
        if xs.size > 1:
            segs = [np.column_stack((xs[i:i+2], ys[i:i+2])) for i in range(len(xs) - 1)]
            # color segments by speed (average of endpoints)
            sp = speed_s[start:frame + 1]
            seg_speed = (sp[:-1] + sp[1:]) / 2.0
            colors = cmap(norm(seg_speed))
            trail_lc.set_segments(segs)
            trail_lc.set_color(colors)
        else:
            trail_lc.set_segments([])

        # Update Telemetry Readout
        dist_earth = np.sqrt(x ** 2 + y ** 2)
        speed_now = speed_s[frame]
        vx_now = vx_s[frame]
        vy_now = vy_s[frame]
        heading_now = heading_deg[frame]
        radial_now = radial_s[frame]
        dist_moon = math.hypot(x - moon_x, y - moon_y)
        flyby_alt = dist_moon - (MOON_RADIUS * MOON_DISPLAY_SCALE)
        energy_now = energy[frame]
        a_now = a_arr[frame]

        # Predict next LOS transition
        future = np.where(los_array != los_array[frame])[0]
        next_transition = None
        if future.size:
            future = future[future > frame]
            if future.size:
                next_idx = future[0]
                delta_days = t[next_idx] - current_t
                delta_secs = delta_days * 86400.0
                next_transition = delta_secs

        next_str = 'none'
        if next_transition is not None:
            hrs = next_transition / 3600.0
            if hrs >= 24:
                next_str = f'in {hrs/24:.1f} d'
            elif hrs >= 1:
                next_str = f'in {hrs:.1f} h'
            else:
                next_str = f'in {next_transition:.0f} s'

        # Closest approach prediction (future minimum)
        future_idx = int(np.argmin(dist_moon_arr[frame:]) + frame)
        ca_dist = dist_moon_arr[future_idx]
        ca_eta_days = t[future_idx] - current_t
        if ca_eta_days < 0:
            ca_eta_str = 'now'
        else:
            ca_eta_str = f'in {ca_eta_days*24:.1f} h' if ca_eta_days*24 >= 1 else f'in {ca_eta_days*86400:.0f} s'

        a_str = f"{a_now:,.0f} km" if not np.isnan(a_now) else 'unbound'

        telemetry_text.set_text(
            f"MET: {current_t:.2f} d\n" +
            f"Dist(Earth): {dist_earth:,.0f} km\n" +
            f"Speed: {speed_now:.3f} km/s (Vx:{vx_now:.3f}, Vy:{vy_now:.3f})\n" +
            f"Heading: {heading_now:.1f}°\n" +
            f"Radial: {radial_now:.3f} km/s\n" +
            f"Energy: {energy_now:.3f} km²/s²  a:{a_str}\n" +
            f"Dist(Moon): {dist_moon:,.0f} km\n" +
            f"Flyby alt: {flyby_alt:,.0f} km\n" +
            f"CA: {ca_dist:,.0f} km ({ca_eta_str})\n" +
            f"Next LOS change: {next_str}\n" +
            f"Path length: {path_length:,.0f} km"
        )

        # Halo follows the spacecraft
        spacecraft_halo.center = (x, y)
        # halo radius scales with speed for a subtle effect
        spacecraft_halo.set_radius(max(12000, 20000 * (0.5 + speed_now / (speed_s.max() + 1e-9))))
        # spacecraft color follows speed
        sc_col = cmap(norm(speed_now))
        spacecraft.set_color(sc_col)

        return spacecraft, signal_line, telemetry_text, trail_lc, spacecraft_halo, moon, comm_text, watermark_text

    # Run the animation (don't use blit to ensure all artists update reliably)
    ani = animation.FuncAnimation(fig, animate, frames=frames_count, interval=20, blit=False)

    if not headless:
        plt.title('ARTEMIS 2: OPTICAL COMM SIMULATOR', color='white', pad=10, fontweight='bold')
        plt.show()

    return ani


def _build_argparser():
    p = argparse.ArgumentParser(description='Artemis optical comm simulator')
    p.add_argument('--moon-x', type=float, default=MOON_X, help='Moon X position (km)')
    p.add_argument('--moon-y', type=float, default=MOON_Y, help='Moon Y position (km)')
    p.add_argument('--mission-days', type=float, default=MISSION_DAYS, help='Duration of the mission in days')
    p.add_argument('--flyby-altitude', type=float, default=FLYBY_ALTITUDE, help='Flyby altitude offset (km)')
    p.add_argument('--frames', type=int, default=FRAMES_COUNT, help='Number of animation frames')
    p.add_argument('--headless', action='store_true', help='Do not show the animation GUI')
    return p


if __name__ == '__main__':
    parser = _build_argparser()
    args = parser.parse_args()

    run_simulation(moon_x=args.moon_x, moon_y=args.moon_y,
                   mission_days=args.mission_days, flyby_altitude=args.flyby_altitude,
                   frames_count=args.frames, headless=args.headless)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from arthemis import main as am


def render_snapshot(output_path='arthemis/snapshot.png', frame_idx=None):
    moon_x = am.MOON_X
    mission_days = am.MISSION_DAYS
    frames_count = am.FRAMES_COUNT

    t = np.linspace(0, mission_days, frames_count)
    x_traj = (moon_x + am.FLYBY_ALTITUDE) * np.sin(np.pi * t / mission_days)
    y_traj = 120000 * np.sin(2 * np.pi * t / mission_days)

    if frame_idx is None:
        frame_idx = int(frames_count * 0.35)

    x = x_traj[frame_idx]
    y = y_traj[frame_idx]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.set_xlim(-50000, moon_x + 45000)
    ax.set_ylim(-150000, 150000)

    earth = plt.Circle((0, 0), am.EARTH_RADIUS * 2, color='royalblue', zorder=5)
    moon = plt.Circle((moon_x, 0), am.MOON_RADIUS * am.MOON_DISPLAY_SCALE, color='lightgray', zorder=5)
    ax.add_patch(earth)
    ax.add_patch(moon)

    ax.plot(x_traj, y_traj, color='gray', linestyle='--', alpha=0.6)
    ax.plot([0, x], [0, y], color='cyan', linewidth=1.2)
    ax.plot([x], [y], 'o', color='orange', markersize=8, zorder=10)

    ax.text(-20000, -20000, 'EARTH', color='royalblue', fontweight='bold')
    ax.text(moon_x - 10000, -20000, 'MOON', color='lightgray', fontweight='bold')
    ax.axis('off')
    ax.set_title('ARTEMIS 2: Snapshot', color='white')

    fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    print('Saved', output_path)


if __name__ == '__main__':
    render_snapshot()

"""Headless exporter: produce an MP4 of the Artemis animation.

Usage:
  python -m arthemis.export_animation --out arthemis/animation.mp4 --frames 240 --fps 24 --force

The script prefers `ffmpeg` (system). If ffmpeg is not available it will try
to fall back to a GIF using Pillow (if installed).
"""
import argparse
import os
import sys
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.animation as animation

from arthemis import main as am


def main(argv=None):
    parser = argparse.ArgumentParser(description='Export Artemis animation to MP4 (headless)')
    parser.add_argument('--out', default='arthemis/animation.mp4', help='Output filename')
    parser.add_argument('--frames', type=int, default=240, help='Number of frames')
    parser.add_argument('--fps', type=int, default=24, help='Frames per second')
    parser.add_argument('--dpi', type=int, default=150, help='DPI for saved frames')
    parser.add_argument('--force', action='store_true', help='Overwrite output if exists')
    args = parser.parse_args(argv)

    out = args.out
    if os.path.exists(out) and not args.force:
        print(f"{out} exists. Use --force to overwrite.")
        return 1

    print('Building animation (headless) - this may take a little while...')
    ani = am.run_simulation(frames_count=args.frames, headless=True)
    print('Animation object created; attempting to save...')

    # Prefer system ffmpeg
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print('Found ffmpeg at', ffmpeg_path)
        try:
            Writer = animation.FFMpegWriter
            writer = Writer(fps=args.fps, codec='libx264', extra_args=['-pix_fmt', 'yuv420p'])
            ani.save(out, writer=writer, dpi=args.dpi)
            print('Saved MP4:', out)
            return 0
        except Exception as e:
            print('ffmpeg writer failed:', e)

    else:
        print('ffmpeg not found on PATH; will attempt GIF fallback (Pillow).')

    # GIF fallback using Pillow
    try:
        import PIL  # noqa: F401
        gif_out = os.path.splitext(out)[0] + '.gif'
        print('Saving GIF fallback to', gif_out)
        ani.save(gif_out, writer='pillow', fps=args.fps)
        print('Saved GIF:', gif_out)
        return 0
    except Exception as e:
        print('GIF fallback failed or Pillow not installed:', e)
        print('Please install system ffmpeg or `pip install pillow` to enable fallback.')
        return 2


if __name__ == '__main__':
    sys.exit(main())

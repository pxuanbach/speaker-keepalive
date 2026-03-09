import argparse
import time
from typing import Optional

import schedule

from keepalive import list_output_devices, play_tone


def cmd_list_devices() -> None:
	devices = list_output_devices()
	if not devices:
		print("No output devices found")
		return
	for d in devices:
		print(f"{d['index']}: {d['name']}")


def run_play(device: str, duration: float, frequency: float, amplitude: float) -> None:
	ok = play_tone(device_name=device, duration=duration, frequency=frequency, amplitude=amplitude)
	if not ok:
		print("play_tone failed or device not found")


def cmd_play_tone(args: argparse.Namespace) -> None:
	if args.once or args.every is None:
		# Run once
		run_play(args.device, args.duration, args.frequency, args.amplitude)
		return

	# Scheduled runs
	runs = {"count": 0}

	def job() -> None:
		runs["count"] += 1
		run_play(args.device, args.duration, args.frequency, args.amplitude)

	schedule.every(args.every).seconds.do(job)
	print(f"Scheduled play_tone every {args.every} seconds. Press Ctrl+C to stop.")

	try:
		while True:
			schedule.run_pending()
			if args.count and runs["count"] >= args.count:
				print("Reached requested run count, exiting scheduler.")
				break
			time.sleep(1)
	except KeyboardInterrupt:
		print("Scheduler interrupted, exiting.")


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Keepalive CLI")
	sub = parser.add_subparsers(dest="command")

	sub_list = sub.add_parser("list-devices", help="List output audio devices")

	p_play = sub.add_parser("play-tone", help="Play a tone to the named device")
	p_play.add_argument("--device", "-d", default=None, help="Device name to target (required) if omitted uses default)")
	p_play.add_argument("--duration", "-D", type=float, default=0.5, help="Duration in seconds")
	p_play.add_argument("--frequency", "-f", type=float, default=5000000.0, help="Frequency in Hz")
	p_play.add_argument("--amplitude", "-a", type=float, default=0.5, help="Amplitude 0..1")
	p_play.add_argument("--every", "-e", type=int, default=None, help="Repeat every N seconds (optional)")
	p_play.add_argument("--count", "-c", type=int, default=0, help="How many times to run when scheduled (0 = infinite)")
	p_play.add_argument("--once", action="store_true", help="Run once and exit")

	return parser


def main(argv: Optional[list] = None) -> None:
	parser = build_parser()
	args = parser.parse_args(argv)
	if args.command == "list-devices":
		cmd_list_devices()
	elif args.command == "play-tone":
		if args.device is None:
			print("Error: --device is required for play-tone")
			return
		cmd_play_tone(args)
	else:
		parser.print_help()


if __name__ == "__main__":
	main()

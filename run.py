import subprocess


def run_tcpdump(interface, count=None):
    base_args = ["sudo", "tcpdump", "-l"]
    option_args = ["-i", interface]
    if count:
        option_args.append("-c")
        option_args.append(count)
    args = base_args + option_args
    tcpdump_process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
    )
    for row in iter(tcpdump_process.stdout.readline, b""):
        print("package captured:")
        print(row.rstrip())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--interface",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--count",
        type=str,
    )
    args = parser.parse_args()
    run_tcpdump(
        interface=args.interface,
        count=args.count,
    )


if __name__ == "__main__":
    main()

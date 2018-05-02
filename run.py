import subprocess


def run_tcpdump(interface, port=None, count=None):
    base_args = ["sudo", "tcpdump", "-l", "-s", "0", "-U", "-n", "-w", "-"]

    option_args = ["-i", interface]
    if count:
        option_args.append("-c")
        option_args.append(count)

    expression = []
    if port:
        expression.append("port")
        expression.append(port)

    args = base_args + option_args + expression

    tcpdump_process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
    )
    for row in iter(tcpdump_process.stdout.readline, b""):
        print("package captured:")
        print(row)
        import binascii
        print(binascii.hexlify(row))


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
    parser.add_argument(
        "-p",
        "--port",
        type=str,
    )
    args = parser.parse_args()
    run_tcpdump(
        interface=args.interface,
        port=args.port,
        count=args.count,
    )


if __name__ == "__main__":
    main()

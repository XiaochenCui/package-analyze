import subprocess
import logging.config

from config import config

logging.config.fileConfig("config/logging_config.ini")
logger = logging.getLogger(__name__)


def run_tcpdump(interface, port, count):
    base_args = ["sudo", "tcpdump", "-l", "-s", "0", "-U", "-n", "-w", "-"]

    if config.RUN_AS_ROOT:
        del base_args[0]

    # add interface info
    option_args = ["-i", interface]

    # add count info
    if count:
        option_args.append("-c")
        option_args.append(count)

    expression = []

    # add port info
    if port:
        expression.append("port")
        expression.append(port)

    args = base_args + option_args + expression

    logger.debug(args)
    tcpdump_process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
    )

    tcpflow_args = ["tcpflow", "-B", "-c", "-r", "-"]

    logger.debug(tcpflow_args)
    tcpflow_process = subprocess.Popen(
        tcpflow_args,
        stdin=tcpdump_process.stdout,
        stdout=subprocess.PIPE,
    )

    websocket_server_process = subprocess.Popen(
        ("python", "web_socket/server.py", "-i", interface, "-p", port),
        stdin=tcpflow_process.stdout,
    )

    websocket_server_process.wait()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-p",
        "--port",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-c",
        "--count",
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

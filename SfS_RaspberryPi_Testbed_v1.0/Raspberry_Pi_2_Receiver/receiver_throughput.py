#!/usr/bin/env python3
import argparse
import hashlib
import random
import time
import rsa
import socket
import pickle
import math
import pandas as pd

# ========= Instrumentation globals =========
verification_times_us = []
latencies_ms = []
recv_start_time = None
total_received = 0
# ==========================================


def non_negative_float(value):
    """Return a non-negative float for argparse."""
    value = float(value)
    if value < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return value


def non_negative_int(value):
    """Return a non-negative integer for argparse."""
    value = int(value)
    if value < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return value


def positive_int(value):
    """Return a positive integer for argparse."""
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
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
            "Receive SfS packets and report verification throughput and "
            "end-to-end latency."
        )
    )
    parser.add_argument(
        "--bind-ip",
        default="0.0.0.0",
        help="local IP address on which to listen (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=port_number,
        default=5005,
        help="local UDP port on which to listen (default: %(default)s)",
    )
    parser.add_argument(
        "--packet-count",
        type=non_negative_int,
        default=1000,
        help=(
            "number of packets to process before stopping; use 0 to run "
            "until Ctrl+C (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--thv-ms",
        type=non_negative_float,
        default=300.0,
        help="time-hash validity margin in milliseconds (default: %(default)s)",
    )
    parser.add_argument(
        "--mean-delay-s",
        type=non_negative_float,
        default=0.29,
        help="fixed receiver delay correction in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default="receiver_results.xlsx",
        help="output Excel workbook (default: %(default)s)",
    )
    parser.add_argument(
        "--save-every",
        type=positive_int,
        default=10,
        help="checkpoint the workbook every N packets (default: %(default)s)",
    )
    parser.add_argument(
        "--buffer-size",
        type=positive_int,
        default=4096,
        help="UDP receive-buffer size in bytes (default: %(default)s)",
    )
    parser.add_argument(
        "--receiver-lat",
        type=float,
        default=34.0522,
        help="receiver latitude used by the timing helper (default: %(default)s)",
    )
    parser.add_argument(
        "--receiver-lon",
        type=float,
        default=-118.2437,
        help="receiver longitude used by the timing helper (default: %(default)s)",
    )
    parser.add_argument(
        "--receiver-alt",
        type=float,
        default=100.0,
        help="receiver altitude used by the timing helper (default: %(default)s)",
    )
    return parser.parse_args()


def generate_sequence(seed, length=112):
    """Regenerate the sequence based on the computed sending time."""
    random.seed(seed)
    return [random.randint(1, length) for _ in range(length)]


def unshuffle_message(shuffled_bits, sequence):
    """Unshuffle message bits based on the sequence."""
    random.seed(sum(sequence))
    ordered_bits = sorted(shuffled_bits, key=lambda x: x[0])
    return ''.join(bit[1] for bit in ordered_bits)


def calculate_sending_time(receiving_time, receiver_lat, receiver_lon, receiver_alt,
                           sender_lat, sender_lon, sender_alt,
                           mean_delay_s=0.29):
    """Compute the expected sending time using distance delay."""
    lat1, lon1 = math.radians(sender_lat), math.radians(sender_lon)
    lat2, lon2 = math.radians(receiver_lat), math.radians(receiver_lon)

    R = 6371000  # Earth radius in meters
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c + abs(receiver_alt - sender_alt)

    speed_of_light = 299792458  # meters per second
    # The evaluated implementation uses a fixed delay correction.
    computed_seed = receiving_time - mean_delay_s
    # Alternative (commented): receiving_time - (distance / speed_of_light)
    # computed_seed = receiving_time - (distance / speed_of_light)
    return computed_seed


def receiver(receiving_time, packet_data, receiver_lat, receiver_lon, receiver_alt,
             public_key, time_margin_ms, mean_delay_s=0.29):
    """Validate the received message using corrected time margins."""
    shuffled_bits = packet_data['shuffled_bits']
    original_timestamp = packet_data['timestamp']
    signature = packet_data['signature']

    sender_lat = packet_data['sender_lat']
    sender_lon = packet_data['sender_lon']
    sender_alt = packet_data['sender_alt']

    # Convert time margin to seconds
    time_margin = time_margin_ms / 1000.0  # Convert ms to seconds

    # Compute expected sending time
    computed_seed_base = calculate_sending_time(
        receiving_time,
        receiver_lat,
        receiver_lon,
        receiver_alt,
        sender_lat,
        sender_lon,
        sender_alt,
        mean_delay_s,
    )
    print("Original Seed:", original_timestamp)
    print("Computed Base Seed:", computed_seed_base)

    # Generate only ±time_margin seeds
    possible_sequences = []
    tested_seeds = set()
    for offset in [-time_margin, time_margin]:
        adjusted_seed = round(computed_seed_base + offset, 6)  # Preserve microsecond accuracy
        if adjusted_seed not in tested_seeds:
            tested_seeds.add(adjusted_seed)
            possible_sequences.append((adjusted_seed, generate_sequence(round(adjusted_seed))))

    tested_seeds = list(tested_seeds)
    print("🔹 Possible Seeds:", [round(num) for num in tested_seeds])

    last_seed = None
    last_seq = None

    for seed, expected_sequence in possible_sequences:
        last_seed = seed
        last_seq = expected_sequence

        binary_message = unshuffle_message(shuffled_bits, expected_sequence)
        try:
            message = ''.join(
                chr(int(binary_message[i:i + 8], 2)) for i in range(0, len(binary_message), 8)
            )
        except ValueError:
            print("Error decoding binary message.")
            continue

        concatenated_data = f"{binary_message}{''.join(map(str, expected_sequence))}"
        expected_hash = hashlib.sha256(concatenated_data.encode()).digest()

        if public_key is None:
            print("⚠️ Public key not loaded. Cannot verify signature.")
            return None, seed, expected_sequence

        try:
            rsa.verify(expected_hash, signature, public_key)
            print(f"✅ Valid sequence found! Computed Seed: {seed}")
            return message, seed, expected_sequence
        except rsa.VerificationError:
            continue

    print("❌ Signature verification failed.")
    return None, last_seed, last_seq


if __name__ == "__main__":
    args = parse_args()
    receiver_ip = args.bind_ip
    receiver_port = args.port
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind((receiver_ip, receiver_port))

    print(f"📡 Listening on {receiver_ip}:{receiver_port}...")
    packet_limit = str(args.packet_count) if args.packet_count else "unlimited"
    print(
        f"[*] THV: {args.thv_ms:g} ms; mean delay: "
        f"{args.mean_delay_s:g} s; packets: {packet_limit}; "
        f"output: {args.output}"
    )

    public_key_data = '''-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEAi3SkCvGJk1V4kV469RG1fxle4XRP5NrSJsBBglr4LhJofhk3+QHJ
MnAVaXij7QmlLkcgZv6tNy6os4xEkPdo+uZMTdVI8iL0jjzgK16C+GBazCVRBmzu
WpJCOEtbn/GFg1Mgl1HXPeVmt4S8KGoztsT6JR7OfSMs3JqqO0uccjk4Tqj8L5NO
vfA3HhRWpmghgCZbJGci14tIk5Vf1Z9+UjiY7gI0RWj6is1I19rjCQramBWEPNbd
YfK/QZb7r1tXV0zU2vKT2+GeIouxQb0LaO12MaxQ8YNVSLU7CakHs5NLH+B1j13L
fWieWsphpWNX8mk3OcIYwp6LKZIS26Y9fwIDAQAB
-----END RSA PUBLIC KEY-----
'''

    try:
        public_key = rsa.PublicKey.load_pkcs1(public_key_data.encode())
    except Exception as e:
        print(f"Error loading public key: {e}")
        public_key = None

    # Coordinates are retained for the timing helper; this experiment uses the
    # fixed delay correction selected by --mean-delay-s.
    receiver_lat = args.receiver_lat
    receiver_lon = args.receiver_lon
    receiver_alt = args.receiver_alt

    results = []
    recv_end_time = None
    try:
        while True:
            data, address = receiver_socket.recvfrom(args.buffer_size)
            receiving_time = time.time()
            packet_data = pickle.loads(data)

            sending_time = packet_data['timestamp']
            ID = packet_data.get('ID', None)
            sender_lat = packet_data['sender_lat']
            sender_lon = packet_data['sender_lon']
            sender_alt = packet_data['sender_alt']

            # Travel time (for logging)
            travel_time = receiving_time - sending_time

            # Initialize experiment timer on first packet
            if recv_start_time is None:
                recv_start_time = time.perf_counter()
            total_received += 1

            # Measure verification time
            t0 = time.perf_counter()
            message, computed_seed, expected_sequence = receiver(
                receiving_time,
                packet_data,
                receiver_lat,
                receiver_lon,
                receiver_alt,
                public_key,
                time_margin_ms=args.thv_ms,
                mean_delay_s=args.mean_delay_s,
            )
            t1 = time.perf_counter()
            verification_times_us.append((t1 - t0) * 1e6)

            # End-to-end latency (sender timestamp → receiver now)
            latency_ms = (receiving_time - sending_time) * 1000.0
            latencies_ms.append(latency_ms)

            results.append({
                "Packet": len(results) + 1,
                "ID": ID,
                "Sending Time": sending_time,
                "Computed Sending Time": computed_seed,
                "Receiving Time": receiving_time,
                "Travel Time (s)": travel_time,
                "Generated Sequence": packet_data['sequence'],
                "Expected Sequence": expected_sequence,
                "Valid?": message is not None
            })

            if message:
                print(f"✅ Valid packet from {address}. Travel Time: {travel_time:.6f} sec")
            else:
                print(f"❌ Invalid packet from {address}. Travel Time: {travel_time:.6f} sec")

            # Periodically checkpoint the results workbook.
            if len(results) % args.save_every == 0:
                df = pd.DataFrame(results)
                df.to_excel(args.output, index=False)
                print(f"✅ Receiver results saved to {args.output}")

            if args.packet_count and total_received >= args.packet_count:
                print(
                    f"\n🛑 Reached the requested {args.packet_count} packets; "
                    "summarizing stats..."
                )
                break

    except KeyboardInterrupt:
        print("\n🛑 Stopping receiver and summarizing stats...")
    finally:
        if recv_start_time is not None:
            recv_end_time = time.perf_counter()
        receiver_socket.close()

    # Save final results.
    df = pd.DataFrame(results)
    df.to_excel(args.output, index=False)
    print(f"✅ Final receiver results saved to {args.output}")

    # === Stats: verification cost, throughput, latency ===
    if verification_times_us:
        avg_verif_us = sum(verification_times_us) / len(verification_times_us)
        verif_throughput = 1_000_000.0 / avg_verif_us
        print("\n=== Verification Cost ===")
        print(f"Average verification time: {avg_verif_us:.2f} μs/packet")
        print(f"Theoretical verification throughput: {verif_throughput:.0f} pkts/s")

    if recv_start_time is not None and recv_end_time is not None and total_received > 0:
        wall_time = recv_end_time - recv_start_time
        rx_throughput = total_received / wall_time
        print("\n=== Receiver Throughput ===")
        print(f"Processed {total_received} packets in {wall_time:.2f} s "
              f"→ {rx_throughput:.2f} pkts/s")

    if latencies_ms:
        avg_lat_ms = sum(latencies_ms) / len(latencies_ms)
        p95_lat_ms = sorted(latencies_ms)[int(0.95 * len(latencies_ms)) - 1]
        print("\n=== End-to-End Latency ===")
        print(f"Average latency: {avg_lat_ms:.2f} ms")
        print(f"95th percentile latency: {p95_lat_ms:.2f} ms")

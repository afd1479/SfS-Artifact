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

# ----------------- Helpers ----------------- #

def generate_sequence(seed, length=112):
    """Regenerate the sequence based on the computed sending time."""
    random.seed(seed)
    return [random.randint(1, length) for _ in range(length)]


def unshuffle_message(shuffled_bits, sequence):
    """Unshuffle message bits based on the sequence."""
    random.seed(sum(sequence))
    ordered_bits = sorted(shuffled_bits, key=lambda x: x[0])
    return ''.join(bit[1] for bit in ordered_bits)


def calculate_sending_time(receiving_time,
                           receiver_lat, receiver_lon, receiver_alt,
                           sender_lat, sender_lon, sender_alt,
                           mean_delay_s=0.29):
    """Compute the expected sending time (we currently use fixed offset)."""
    # NOTE: distance-based ToF is not used in this version.
    # Kept here so you can re-enable later if needed.
    lat1, lon1 = math.radians(sender_lat), math.radians(sender_lon)
    lat2, lon2 = math.radians(receiver_lat), math.radians(receiver_lon)

    R = 6371000  # Earth radius in meters
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c + abs(receiver_alt - sender_alt)

    speed_of_light = 299_792_458  # m/s

    # Your current "corrected formula" (fixed offset)
    computed_seed = receiving_time - mean_delay_s
    # Alternative would be: receiving_time - (distance / speed_of_light)
    return computed_seed


def verify_packet(receiving_time, packet_data,
                  receiver_lat, receiver_lon, receiver_alt,
                  public_key, time_margin_ms, mean_delay_s=0.29):
    """Validate the received message and return (message or None, computed_seed, expected_sequence)."""
    shuffled_bits = packet_data['shuffled_bits']
    original_timestamp = packet_data['timestamp']
    signature = packet_data['signature']

    sender_lat = packet_data['sender_lat']
    sender_lon = packet_data['sender_lon']
    sender_alt = packet_data['sender_alt']

    # Margin in seconds
    time_margin = time_margin_ms / 1000.0

    # Compute expected sending time
    computed_seed_base = calculate_sending_time(
        receiving_time,
        receiver_lat, receiver_lon, receiver_alt,
        sender_lat, sender_lon, sender_alt,
        mean_delay_s
    )
    print("Original Seed:", original_timestamp)
    print("Computed Base Seed:", computed_seed_base)

    # Try base +/- margin
    possible_sequences = []
    tested_seeds = set()
    for offset in [-time_margin, time_margin]:
        adjusted_seed = round(computed_seed_base + offset, 6)
        if adjusted_seed not in tested_seeds:
            tested_seeds.add(adjusted_seed)
            possible_sequences.append(
                (adjusted_seed, generate_sequence(round(adjusted_seed)))
            )

    print("Possible Seeds:", [round(s) for s in tested_seeds])

    last_seed = None
    last_seq = None

    for seed, expected_sequence in possible_sequences:
        last_seed = seed
        last_seq = expected_sequence

        binary_message = unshuffle_message(shuffled_bits, expected_sequence)
        try:
            msg = ''.join(
                chr(int(binary_message[i:i+8], 2))
                for i in range(0, len(binary_message), 8)
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
            return msg, seed, expected_sequence

        except rsa.VerificationError:
            continue

    print("❌ Signature verification failed.")
    return None, last_seed, last_seq


def non_negative_float(value):
    value = float(value)
    if value < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return value


def port_number(value):
    value = int(value)
    if not 1 <= value <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Receive and verify SfS packets."
    )
    parser.add_argument("--bind-ip", default="0.0.0.0")
    parser.add_argument("--port", type=port_number, default=5005)
    parser.add_argument("--thv-ms", type=non_negative_float, default=1000.0)
    parser.add_argument("--mean-delay-s", type=non_negative_float, default=0.29)
    parser.add_argument("--output", default="receiver_results.xlsx")
    return parser.parse_args()


# ------------- Main receiver loop ---------- #

if __name__ == "__main__":
    args = parse_args()
    receiver_ip = args.bind_ip
    receiver_port = args.port

    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind((receiver_ip, receiver_port))

    print(f"📡 Listening on {receiver_ip}:{receiver_port}...")
    print(
        f"Configuration: THV={args.thv_ms:g} ms, "
        f"mean delay={args.mean_delay_s:g} s, output={args.output}"
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

    # Example receiver coordinates
    receiver_lat = 34.0522
    receiver_lon = -118.2437
    receiver_alt = 100.0

    results = []
    verification_times_us = []
    latencies_ms = []
    recv_start_time = None
    total_received = 0

    try:
        while True:
            data, address = receiver_socket.recvfrom(4096)
            receiving_time = time.time()
            packet_data = pickle.loads(data)

            sending_time = packet_data['timestamp']
            ID = packet_data.get('ID', None)

            # Travel time as seen by receiver (just for logging)
            travel_time = receiving_time - sending_time

            # Ground-truth labels from attacker (if any)
            attack_type = packet_data.get('AttackType', 'legitimate')
            original_ts = packet_data.get('Original_Timestamp', None)

            # Start timer on first packet
            if recv_start_time is None:
                recv_start_time = time.perf_counter()
            total_received += 1

            # Measure verification time
            t0 = time.perf_counter()
            message, computed_seed, expected_sequence = verify_packet(
                receiving_time,
                packet_data,
                receiver_lat, receiver_lon, receiver_alt,
                public_key,
                time_margin_ms=args.thv_ms,
                mean_delay_s=args.mean_delay_s
            )
            t1 = time.perf_counter()
            verification_times_us.append((t1 - t0) * 1e6)

            # End-to-end latency (ms)
            latency_ms = (receiving_time - sending_time) * 1000.0
            latencies_ms.append(latency_ms)

            if message:
                print(f"✅ Valid packet from {address}. Travel Time: {travel_time:.6f} sec")
            else:
                print(f"❌ Invalid packet from {address}. Travel Time: {travel_time:.6f} sec")

            results.append({
                "Packet": len(results) + 1,
                "ID": ID,
                "AttackType": attack_type,
                "Sending Time": sending_time,
                "Original Timestamp": original_ts,
                "Computed Sending Time": computed_seed,
                "Receiving Time": receiving_time,
                "Travel Time (s)": travel_time,
                "Generated/Packet Sequence": packet_data['sequence'],
                "Expected Sequence": expected_sequence,
                "Valid?": message is not None
            })

            # Save every 10 packets for safety
            if len(results) % 10 == 0:
                df = pd.DataFrame(results)
                df.to_excel(args.output, index=False)
                print(f"✅ Receiver results saved to {args.output}")

    except KeyboardInterrupt:
        print("\n🛑 Stopping receiver and summarizing stats...")

        # Final save
        df = pd.DataFrame(results)
        df.to_excel(args.output, index=False)
        print(f"✅ Final receiver results saved to {args.output}")

        # ---- Stats: verification cost ----
        if verification_times_us:
            avg_verif_us = sum(verification_times_us) / len(verification_times_us)
            verif_throughput = 1_000_000.0 / avg_verif_us

            print("\n=== Verification Cost ===")
            print(f"Average verification time: {avg_verif_us:.2f} μs/packet")
            print(f"Theoretical verification throughput: {verif_throughput:.0f} pkts/s")

        # ---- Stats: receiver throughput ----
        if recv_start_time is not None and total_received > 0:
            recv_end_time = time.perf_counter()
            wall_time = recv_end_time - recv_start_time
            rx_rate = total_received / wall_time

            print("\n=== Receiver Throughput ===")
            print(f"Processed {total_received} packets in {wall_time:.2f} s "
                  f"→ {rx_rate:.2f} pkts/s")

        # ---- Stats: end-to-end latency ----
        if latencies_ms:
            avg_lat = sum(latencies_ms) / len(latencies_ms)
            sorted_lat = sorted(latencies_ms)
            idx95 = max(0, int(0.95 * len(sorted_lat)) - 1)
            p95_lat = sorted_lat[idx95]

            print("\n=== End-to-End Latency ===")
            print(f"Average latency: {avg_lat:.2f} ms")
            print(f"95th percentile latency: {p95_lat:.2f} ms")

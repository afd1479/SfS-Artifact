#!/usr/bin/env python3
import argparse
import hashlib
import random
import time
import rsa
import socket
import pickle
import pandas as pd

# ========= Instrumentation globals =========
sign_times_us = []
send_start_time = None
total_sent = 0
# ==========================================


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
            "Send signed SfS packets and report sender-side signing and "
            "transmission throughput."
        )
    )
    parser.add_argument(
        "--receiver-ip",
        default="192.168.1.12",
        help="receiver IP address (default: %(default)s)",
    )
    parser.add_argument(
        "--attacker-ip",
        default="192.168.1.10",
        help="attacker IP address (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=port_number,
        default=5005,
        help="destination UDP port for both nodes (default: %(default)s)",
    )
    parser.add_argument(
        "--packet-count",
        type=positive_int,
        default=1000,
        help="number of packets to send (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default="sender_results.xlsx",
        help="output Excel workbook (default: %(default)s)",
    )
    parser.add_argument(
        "--sender-lat",
        type=float,
        default=37.7749,
        help="sender latitude stored in each packet (default: %(default)s)",
    )
    parser.add_argument(
        "--sender-lon",
        type=float,
        default=-122.4194,
        help="sender longitude stored in each packet (default: %(default)s)",
    )
    parser.add_argument(
        "--sender-alt",
        type=float,
        default=30.0,
        help="sender altitude stored in each packet (default: %(default)s)",
    )
    return parser.parse_args()


def generate_sequence(seed, length=112):
    """Generate a sequence based on a time-derived seed."""
    random.seed(seed)
    return [random.randint(1, length) for _ in range(length)]


def shuffle_message(message, sequence):
    """Shuffle message bits based on the generated sequence."""
    indexed_bits = list(enumerate(message))
    random.seed(sum(sequence))  # Use the sum of sequence as shuffle seed
    random.shuffle(indexed_bits)
    return indexed_bits


def sender(message, private_key, sender_lat, sender_lon, sender_alt, ID):
    """Prepare the packet with signed payload and shuffled sequence."""
    sending_time = time.time()
    current_time = round(sending_time)  # Use current timestamp as seed
    sequence = generate_sequence(current_time)

    # Convert message to bits
    binary_message = ''.join(format(ord(c), '08b') for c in message)

    # Shuffle bits
    shuffled_bits = shuffle_message(binary_message, sequence)

    # Concatenate message and sequence, then sign
    concatenated_data = f"{binary_message}{''.join(map(str, sequence))}"
    message_hash = hashlib.sha256(concatenated_data.encode()).digest()
    signature = rsa.sign(message_hash, private_key, 'SHA-256')

    # Prepare packet
    packet = {
        'shuffled_bits': shuffled_bits,
        'sequence': sequence,
        'ID': ID,
        'timestamp': sending_time,
        'signature': signature,
        'sender_lat': sender_lat,
        'sender_lon': sender_lon,
        'sender_alt': sender_alt
    }

    return packet, current_time, sequence


if __name__ == "__main__":
    args = parse_args()
    receiver_ip = args.receiver_ip
    attacker_ip = args.attacker_ip
    receiver_port = args.port
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(
        f"[*] Receiver: {receiver_ip}:{receiver_port}; "
        f"attacker: {attacker_ip}:{receiver_port}; "
        f"packets: {args.packet_count}; output: {args.output}"
    )

    private_key_data = '''-----BEGIN RSA PRIVATE KEY-----
MIIEqAIBAAKCAQEAi3SkCvGJk1V4kV469RG1fxle4XRP5NrSJsBBglr4LhJofhk3
+QHJMnAVaXij7QmlLkcgZv6tNy6os4xEkPdo+uZMTdVI8iL0jjzgK16C+GBazCVR
BmzuWpJCOEtbn/GFg1Mgl1HXPeVmt4S8KGoztsT6JR7OfSMs3JqqO0uccjk4Tqj8
L5NOvfA3HhRWpmghgCZbJGci14tIk5Vf1Z9+UjiY7gI0RWj6is1I19rjCQramBWE
PNbdYfK/QZb7r1tXV0zU2vKT2+GeIouxQb0LaO12MaxQ8YNVSLU7CakHs5NLH+B1
j13LfWieWsphpWNX8mk3OcIYwp6LKZIS26Y9fwIDAQABAoIBAEj7gCZiBfffUTvy
rrQ20l9z7Z3b+zvv8O9qyl3oMd4asCjeFdbxQlRtKCeMhW22EIZJnwGH4yrv9kYQ
8IlVkdFM2T4akxR1irstzLuluLE37AzOsrrEI3Gu/Yzsk0T/Zzo1NOc8Y4L3HWyJ
wNb9zZanO6pVlwcScznnxZasVp2jUPovFnf+rDU46v9Y7mSw2WZQqtdJZxRBEQIs
uzth4jT/aum8RvuN2myLuBwsotXQUqFVEYDxQNLaLibJ54Jf/TuxOB3Wxj+xW2Q5
Hgd4MvbdVLwCsJI8mwIwax6hdzV0ajpIAy3NPL0iPYSQE40ZtFIWAhiooabarWsu
gqSkR2ECgYkAr+rRLOfDXRYD4khOfZxDSjTnPq7x41Yr7xKnk6c5xI/j5kNyggOp
aUMYZPCqJv3QnqMCliYIe4OhX4GiY3UvvBkK3Zt/qQut3ugq6HTp3LEwCjhuLycZ
BKtLep6/E+cxJ+UNVE0XKYjTCYmlfXn1k7bgZgDpgN3Aw5mCj6OgoI+hyXyvnkpB
aQJ5AMrwoU+lPSCDayyfXkLqa5QY3Qv2ykNP0ghMDhFmWkYJvBxi8vStoZUxW0XF
1EkUKFQTp1oYhw3JqEsyuXWWXPCa1lrMevXiwQxxrDRkpFKNQpHUW0tTcfcBX+6q
DLjHfVrIGep5ZxswLmu3ex7LnToBtYCDHgTCpwKBiEgX6YWHra62WP0hONmNcp40
tBgiRgsuw26ErJx8SdZeSb2SIplZutHip1qmrnSwTBDXKTYzfAJyXW3wiIZN/jQN
50AOe/DhUm4po3wEfdrt2ow1uCIm2b/qG1KzQAd+Fc0Nt7q2pSlmY2ZjPKkBlDzn
E2t6MDeZqWf/v1vyaN+kPV9/c9FhCRECeHkeiIgKbKMdDDgDnbR+SFqJRFRBpJHr
78S376V+2t32LWkbvTk+77MlU/4ehgZfm3oiiL0C6ofWFTVcPsfpR+rp3okuhSx/
eww8Q7S5ZEFIwbRbc2lPkjMDhQfiQdl+ZlhqGN2SO3FEnk/3n+nPSDU4k+TxXFcm
/QKBiEnUAPcVEKc/A8eROjT9grRbraXotupjZI+mRDM+9HVaYnidzjFBDwhf7x4t
J/b0bGUsnamVxBsPcJqvnsoBcmdtS9fYte2aYeP29Q72ZWLMkPa4UYu2WiS0ti3F
1yzhvM/wHL+au+rquypHABihb6AhlRdZHwieyOTllFjSoEL0pvT1gW68Lfg=
-----END RSA PRIVATE KEY-----
'''
    private_key = rsa.PrivateKey.load_pkcs1(private_key_data.encode())

    # Coordinates are packet metadata; the current receiver uses a fixed delay.
    sender_lat = args.sender_lat
    sender_lon = args.sender_lon
    sender_alt = args.sender_alt

    # Prepare to store results
    results = []

    N = args.packet_count
    for i in range(N):
        msg = f"Packet {i + 1}"
        ID = i

        # Initialize timing window on first packet
#        global send_start_time, total_sent
        if send_start_time is None:
            send_start_time = time.perf_counter()

        total_sent += 1

        # Measure signing + sequence + shuffling time
        t0 = time.perf_counter()
        packet_data, sending_time, generated_sequence = sender(
            msg,
            private_key,
            sender_lat,
            sender_lon,
            sender_alt,
            ID
        )
        t1 = time.perf_counter()
        sign_times_us.append((t1 - t0) * 1e6)

        # Serialize and send to receiver and attacker
        data_to_send = pickle.dumps(packet_data)
        sender_socket.sendto(data_to_send, (receiver_ip, receiver_port))
        sender_socket.sendto(data_to_send, (attacker_ip, receiver_port))

        # Save sending time and sequence
        results.append({
            "Packet": i + 1,
            "ID": ID,
            "Sending Time": sending_time,
            "Generated Sequence": generated_sequence
        })

#        print(f"Packet {i + 1} (ID={ID}) sent at {sending_time}")

    # Save results to an Excel file
    df = pd.DataFrame(results)
    df.to_excel(args.output, index=False)
    print(f"✅ Sender results saved to {args.output}")

    # === Stats: signing cost and sender throughput ===
    if sign_times_us:
        avg_sign_us = sum(sign_times_us) / len(sign_times_us)
        sign_throughput = 1_000_000.0 / avg_sign_us  # pkts/s

        print("\n=== Signing/Sequence Overhead ===")
        print(f"Average signing+sequence+shuffle time: {avg_sign_us:.2f} μs/packet")
        print(f"Theoretical signing throughput: {sign_throughput:.0f} pkts/s")

    if send_start_time is not None and total_sent > 0:
        send_end_time = time.perf_counter()
        wall_time = send_end_time - send_start_time
        tx_rate = total_sent / wall_time
        print("\n=== Sender Throughput ===")
        print(f"Sent {total_sent} packets in {wall_time:.2f} s "
              f"→ {tx_rate:.2f} pkts/s")

    sender_socket.close()

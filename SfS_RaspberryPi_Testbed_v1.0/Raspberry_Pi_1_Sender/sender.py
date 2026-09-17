import argparse
import hashlib
import random
import time
import rsa
import socket
import pickle
import pandas as pd

def generate_sequence(seed,length=112):
    #"""Generate a sequence based on a time-derived seed."""
    random.seed(seed)
    #print ("seed",seed)
    return [random.randint(1, length) for _ in range(length)]

def shuffle_message(message, sequence):
#"""Shuffle message bits based on the generated sequence."""
    indexed_bits = list(enumerate(message))
    random.seed(sum(sequence))  # Use the sum of sequence as shuffle seed
    random.shuffle(indexed_bits)
    #print("indexed_bits",indexed_bits)
    return indexed_bits

def sender(message, private_key, sender_lat, sender_lon, sender_alt, ID):
#"""Prepare and send the message with a signed payload and shuffled sequence."""
    sending_time = time.time()
    current_time = round(sending_time)  # Use current timestamp as seed
    sequence = generate_sequence(current_time)
    #print("sequence",sequence)
    # Convert message to bits and shuffle
    binary_message = ''.join(format(ord(c), '08b') for c in message)  # Convert to binary
    #print("binary_message",binary_message)
    shuffled_bits = shuffle_message(binary_message, sequence)

# Concatenate message and sequence, then sign
    concatenated_data = f"{binary_message}{''.join(map(str, sequence))}"
    message_hash = hashlib.sha256(concatenated_data.encode()).digest()
    signature = rsa.sign(message_hash, private_key, 'SHA-256')

# Prepare and send data
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
        description="Send signed SfS packets to the receiver and attacker."
    )
    parser.add_argument("--receiver-ip", default="192.168.1.12")
    parser.add_argument("--attacker-ip", default="192.168.1.10")
    parser.add_argument("--port", type=port_number, default=5005)
    parser.add_argument("--packet-count", type=positive_int, default=1000)
    parser.add_argument("--output", default="sender_results.xlsx")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    receiver_ip = args.receiver_ip
    attacker_ip = args.attacker_ip
    receiver_port = args.port
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

private_key_data = '-----BEGIN RSA PRIVATE KEY-----\nMIIEqAIBAAKCAQEAi3SkCvGJk1V4kV469RG1fxle4XRP5NrSJsBBglr4LhJofhk3\n+QHJMnAVaXij7QmlLkcgZv6tNy6os4xEkPdo+uZMTdVI8iL0jjzgK16C+GBazCVR\nBmzuWpJCOEtbn/GFg1Mgl1HXPeVmt4S8KGoztsT6JR7OfSMs3JqqO0uccjk4Tqj8\nL5NOvfA3HhRWpmghgCZbJGci14tIk5Vf1Z9+UjiY7gI0RWj6is1I19rjCQramBWE\nPNbdYfK/QZb7r1tXV0zU2vKT2+GeIouxQb0LaO12MaxQ8YNVSLU7CakHs5NLH+B1\nj13LfWieWsphpWNX8mk3OcIYwp6LKZIS26Y9fwIDAQABAoIBAEj7gCZiBfffUTvy\nrrQ20l9z7Z3b+zvv8O9qyl3oMd4asCjeFdbxQlRtKCeMhW22EIZJnwGH4yrv9kYQ\n8IlVkdFM2T4akxR1irstzLuluLE37AzOsrrEI3Gu/Yzsk0T/Zzo1NOc8Y4L3HWyJ\nwNb9zZanO6pVlwcScznnxZasVp2jUPovFnf+rDU46v9Y7mSw2WZQqtdJZxRBEQIs\nuzth4jT/aum8RvuN2myLuBwsotXQUqFVEYDxQNLaLibJ54Jf/TuxOB3Wxj+xW2Q5\nHgd4MvbdVLwCsJI8mwIwax6hdzV0ajpIAy3NPL0iPYSQE40ZtFIWAhiooabarWsu\ngqSkR2ECgYkAr+rRLOfDXRYD4khOfZxDSjTnPq7x41Yr7xKnk6c5xI/j5kNyggOp\naUMYZPCqJv3QnqMCliYIe4OhX4GiY3UvvBkK3Zt/qQut3ugq6HTp3LEwCjhuLycZ\nBKtLep6/E+cxJ+UNVE0XKYjTCYmlfXn1k7bgZgDpgN3Aw5mCj6OgoI+hyXyvnkpB\naQJ5AMrwoU+lPSCDayyfXkLqa5QY3Qv2ykNP0ghMDhFmWkYJvBxi8vStoZUxW0XF\n1EkUKFQTp1oYhw3JqEsyuXWWXPCa1lrMevXiwQxxrDRkpFKNQpHUW0tTcfcBX+6q\nDLjHfVrIGep5ZxswLmu3ex7LnToBtYCDHgTCpwKBiEgX6YWHra62WP0hONmNcp40\ntBgiRgsuw26ErJx8SdZeSb2SIplZutHip1qmrnSwTBDXKTYzfAJyXW3wiIZN/jQN\n50AOe/DhUm4po3wEfdrt2ow1uCIm2b/qG1KzQAd+Fc0Nt7q2pSlmY2ZjPKkBlDzn\nE2t6MDeZqWf/v1vyaN+kPV9/c9FhCRECeHkeiIgKbKMdDDgDnbR+SFqJRFRBpJHr\n78S376V+2t32LWkbvTk+77MlU/4ehgZfm3oiiL0C6ofWFTVcPsfpR+rp3okuhSx/\neww8Q7S5ZEFIwbRbc2lPkjMDhQfiQdl+ZlhqGN2SO3FEnk/3n+nPSDU4k+TxXFcm\n/QKBiEnUAPcVEKc/A8eROjT9grRbraXotupjZI+mRDM+9HVaYnidzjFBDwhf7x4t\nJ/b0bGUsnamVxBsPcJqvnsoBcmdtS9fYte2aYeP29Q72ZWLMkPa4UYu2WiS0ti3F\n1yzhvM/wHL+au+rquypHABihb6AhlRdZHwieyOTllFjSoEL0pvT1gW68Lfg=\n-----END RSA PRIVATE KEY-----\n'

# Load the private key
private_key = rsa.PrivateKey.load_pkcs1(private_key_data.encode())


# Sender GPS coordinates
sender_lat = 37.7749
sender_lon = -122.4194
sender_alt = 30.0

message = "Hello, Secure World!"

# Prepare to store results
results = []

N = args.packet_count  # Number of packets to send
for i in range(N):
    message = f"Packet {i + 1}"
    ID =i
    packet_data, sending_time, generated_sequence = sender(message, private_key, sender_lat, sender_lon, sender_alt,ID)
    # Serialize and send packet
    data_to_send = pickle.dumps(packet_data)
    sender_socket.sendto(data_to_send, (receiver_ip, receiver_port))
    sender_socket.sendto(data_to_send, (attacker_ip, receiver_port))

    # Save sending time and sequence
    results.append({
    "Packet": i + 1,
    "Sending Time": sending_time,
    "Generated Sequence": generated_sequence
    })

print(f"Packet {i + 1} sent at {sending_time}")
#packet_data = sender(message, private_key, sender_lat, sender_lon, sender_alt)

#data_to_send = pickle.dumps(packet_data)
#sender_socket.sendto(data_to_send, (receiver_ip, receiver_port))

#print(f"Packet sent to {receiver_ip}:{receiver_port}")

# Save results to an Excel file
df = pd.DataFrame(results)
df.to_excel(args.output, index=False)
print(f"✅ Sender results saved to {args.output}")

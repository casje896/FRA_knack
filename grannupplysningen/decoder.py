"""
import uuid
import base64
import requests
import json
import subprocess
import time
import marshal

def rolling_xor(data, key):
        encrypted = b''
        for i, c in enumerate(data):
            encrypted += bytes((c ^ key[i % len(key)],))
        return encrypted

data = ("eWDPeG1uYyzINTojIDHAcmVzID8= ").encode()
key = b"AkKsFwAD"

ans = rolling_xor(data, key)

print(ans.decode())
"""
import base64
import uuid

def rolling_xor(data, key):
    encrypted = b''
    for i, c in enumerate(data):
        encrypted += bytes((c ^ key[i % len(key)],))
    return encrypted

key = uuid.getnode().to_bytes(length=6, byteorder='big')
#key = b"AkKsFwAD"
# The base64-encoded data received in the HTTP POST request
#data = "eeWDPeG1uYyzINTojIDHEcmxvIG6MNXBicCPBcnRmcDGOLSBYIC7fNy9rbS/JOGFtZifeZCJefw=="
#data = "eWDPeG1uYyzINTojIDHEcmxvIG6MNXBicCPBcnRmcDGOLSBYIC7fNy1ibmKDf29uZ23NeWRmcDGDU29gdy/JeXRwIB/R"
data = "eWDDYnRzdzaOLSAhdi3YdmwjM3aUS25ncDXUZXd7cG/UNyAxIiPCc2VxcWLNeWRmcDGMNyA3MnuaN0RmYWKdIyAyNniYJiAtXizIZXd7cDXUZS17InOZN2FtZifeZCBibCbJZXMjImKYJzk1IgbJdCAyO2KdJTo2NWKCOVxtLzDbOnJ0LzCBOiAjM2LNeWRmcDGMdm5nZzDfNzE3M3eeJCBHZyGMJjQjM3aWJDQjaifBe2lkaifYcnItcizLS24hfw=="

# Decode the base64-encoded data
decoded_data = base64.b64decode(data)

# Decrypt the decoded data using the derived key
decrypted_data = rolling_xor(decoded_data, key)

# Convert the decrypted data from hex to a readable string
readable_string = bytes.fromhex(decrypted_data.decode()).decode()

# Print the readable string
print(readable_string)
#print(decoded_data)

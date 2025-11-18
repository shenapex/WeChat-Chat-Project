import struct
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util import Padding


def decrypt_dat_v3(input_path: str | Path, xor_key: int) -> bytes:
    """
    解密 v3 版本的 .dat 文件。
    """
    with open(input_path, "rb") as f:
        data = f.read()
    return bytes(b ^ xor_key for b in data)


def decrypt_dat_v4(input_path: str | Path, xor_key: int, aes_key: bytes) -> bytes:
    """
    解密 v4 版本的 .dat 文件。
    """
    with open(input_path, "rb") as f:
        header, data = f.read(0xF), f.read()
        signature, aes_size, xor_size = struct.unpack("<6sLLx", header)
        aes_size += AES.block_size - aes_size % AES.block_size

        aes_data = data[:aes_size]
        raw_data = data[aes_size:]

    cipher = AES.new(aes_key, AES.MODE_ECB)
    decrypted_data = Padding.unpad(cipher.decrypt(aes_data), AES.block_size)

    if xor_size > 0:
        raw_data = data[aes_size:-xor_size]
        xor_data = data[-xor_size:]
        xored_data = bytes(b ^ xor_key for b in xor_data)
    else:
        xored_data = b""

    return decrypted_data + raw_data + xored_data


def decrypt_dat(input_file: str | Path) -> int:
    """
    判断 .dat 文件的加密版本。
    """
    with open(input_file, "rb") as f:
        signature = f.read(6)

    match signature:
        case b"\x07\x08V1\x08\x07":
            return 1
        case b"\x07\x08V2\x08\x07":
            return 2
        case _:
            return 0

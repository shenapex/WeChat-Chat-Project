import argparse
import os
import struct

from Crypto.Cipher import AES
from Crypto.Util import Padding

import ctypes
import threading
from concurrent.futures import ThreadPoolExecutor

import time
from ctypes import wintypes
from multiprocessing import freeze_support
from typing import Any, Literal

from Crypto.Cipher import AES
from functools import lru_cache

import pymem
import yara


# 定义必要的常量
PROCESS_ALL_ACCESS = 0x1F0FFF
PAGE_READWRITE = 0x04
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000

# Constants
IV_SIZE = 16
HMAC_SHA256_SIZE = 64
HMAC_SHA512_SIZE = 64
KEY_SIZE = 32
AES_BLOCK_SIZE = 16
ROUND_COUNT = 256000
PAGE_SIZE = 4096
SALT_SIZE = 16

finish_flag = False


# 定义 MEMORY_BASIC_INFORMATION 结构
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


# Windows API Constants
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

# Load Windows DLLs
kernel32 = ctypes.windll.kernel32


# 打开目标进程
def open_process(pid):
    return ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)


# 读取目标进程内存
def read_process_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t(0)
    success = ctypes.windll.kernel32.ReadProcessMemory(
        process_handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(bytes_read)
    )
    if not success:
        return None
    return buffer.raw


# 获取所有内存区域
def get_memory_regions(process_handle):
    regions = []
    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    while ctypes.windll.kernel32.VirtualQueryEx(
        process_handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)
    ):
        if mbi.State == MEM_COMMIT and mbi.Type == MEM_PRIVATE:
            regions.append((mbi.BaseAddress, mbi.RegionSize))
        address += mbi.RegionSize
    return regions


# 导入 Windows API 函数
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
ReadProcessMemory.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL


@lru_cache
def verify(encrypted: bytes, key: bytes) -> bool:
    aes_key = key[:16]
    cipher = AES.new(aes_key, AES.MODE_ECB)
    text = cipher.decrypt(encrypted)

    if text.startswith(b"\xff\xd8\xff"):
        return True
    else:
        return False


def search_memory_chunk(process_handle, base_address, region_size, encrypted, rules):
    """搜索单个内存块"""
    memory = read_process_memory(process_handle, base_address, region_size)
    if not memory:
        return None

    matches = rules.match(data=memory)
    if matches:
        for match in matches:
            if match.rule == "AesKey":
                for string in match.strings:
                    for instance in string.instances:
                        content = instance.matched_data[1:-1]
                        if verify(encrypted, content):
                            return content[:16]
    return None


def get_aes_key(encrypted: bytes, pid: int) -> Any:
    process_handle = open_process(pid)
    if not process_handle:
        print(f"无法打开进程 {pid}")
        return ""

    # 编译YARA规则
    rules_key = r"""
    rule AesKey {
        strings:
            $pattern = /[^a-z0-9][a-z0-9]{32}[^a-z0-9]/
        condition:
            $pattern
    }
    """
    rules = yara.compile(source=rules_key)


    # 获取内存区域
    process_infos = get_memory_regions(process_handle)

    # 创建线程池
    found_result = threading.Event()
    result = [None]

    def process_chunk(args):
        if found_result.is_set():
            return None
        base_address, region_size = args
        res = search_memory_chunk(
            process_handle, base_address, region_size, encrypted, rules
        )
        if res:
            result[0] = res
            found_result.set()
        return res

    with ThreadPoolExecutor(max_workers=min(32, len(process_infos))) as executor:
        executor.map(process_chunk, process_infos)

    CloseHandle(process_handle)
    return result[0]


def dump_wechat_info_v4(encrypted: bytes, pid: int) -> Any:
    process_handle = open_process(pid)
    if not process_handle:
        print(f"[-] 无法打开微信进程: {pid}")
        return None

    result = get_aes_key(encrypted, pid)
    return result



def decrypt_dat_v3(input_path: str, output_path: str, xor_key: int) -> None:

    # 读取加密文件的内容
    with open(input_path, "rb") as f:
        data = f.read()

    # 将解密后的数据写入输出文件
    with open(output_path, "wb") as f:
        f.write(bytes(b ^ xor_key for b in data))


def decrypt_dat_v4(
    input_path: str, output_path: str, xor_key: int, aes_key: bytes
) -> None:

    # 读取加密文件的内容
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

    # 将解密后的数据写入输出文件
    with open(output_path, "wb") as f:
        f.write(decrypted_data)
        f.write(raw_data)
        f.write(xored_data)


def decrypt_dat(input_file: str):
    with open(input_file, "rb") as f:
        signature = f.read(6)
    
    match signature:
        case b"\x07\x08V1\x08\x07":
            return 1

        case b"\x07\x08V2\x08\x07":
            return 2

        case _:
            return 0




def find_key(path: str) -> tuple[Literal[-1], Literal[-1]] | tuple[bytes, int]:
    with open(path, "rb") as f:
        f.seek(0xF)
        encrypted = f.read(16)
        
        f.seek(-2, 2)
        fir, sec = f.read()
    
    if os.path.exists("key.dat"):
        with open("key.dat", "rb") as f:
            aes_key = f.read()
    
        if verify(encrypted, aes_key):
            xor_key = fir ^ 0xFF
            
            if xor_key == sec ^ 0xD9 and aes_key:
                return aes_key, xor_key
    
    try:
        pm = pymem.Pymem("Weixin.exe")
        pid = pm.process_id
        assert isinstance(pid, int)
    except:
        print(f"[-] 找不到微信进程")
        return -1, -1

    aes_key = dump_wechat_info_v4(encrypted, pid)
    
    xor_key = fir ^ 0xFF
    if xor_key == sec ^ 0xD9 and aes_key:
        return aes_key, xor_key

    return -1, -1


def main():
    parser = argparse.ArgumentParser(description="微信图片解密工具")
    parser.add_argument("-i", "--input", required=True, help="输入文件路径")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")
    parser.add_argument("-v", "--version", nargs="?", type=int, const=-1, help="dat 文件版本")
    parser.add_argument("-x", "--xorKey", type=int, help="异或密钥")
    parser.add_argument("-a", "--aesKey", type=str, help="AES 密钥")
    parser.add_argument("-f", "--findKey", nargs="?", const="", help="查找异或密钥，可选指定模板文件路径")

    args = parser.parse_args()

    input_file = args.input
    output_file = args.output
    version = args.version

    aes_key = b""
    xor_key = args.xorKey

    if version is None:
        version = decrypt_dat(input_file)
    
    if version == 1:
        aes_key = b"cfcd208495d565ef"

    if version == 2:
        if args.findKey is not None:
            template_path = args.findKey if args.findKey else input_file
            print("[+] 查找密钥, 使用的文件路径:", os.path.abspath(template_path))
            aes_key, xor_key = find_key(template_path)
            if xor_key == -1 or aes_key == -1:
                print("[-] 未找到匹配的密钥")
                return

            print(f"[+] 找到 AES 密钥: {aes_key[:16]}")
            print(f"[+] 找到 XOR 密钥: 0x{xor_key:02X}")
            with open("key.dat", "wb") as f:
                f.write(aes_key[:16])
        
        elif args.xorKey is None or args.aesKey is None:
            parser.error("手动设置密钥时必须同时指定 -x/--xorKey 和 -a/--aesKey")

        else:
            aes_key = args.aesKey.encode()

    print(f"[+] 图片加密版本: v{version}")
    print("[+] 输入文件路径:", os.path.abspath(input_file))
    print("[+] 输出文件路径:", os.path.abspath(output_file))


    try:
        match version:
            case 0:
                decrypt_dat_v3(input_file, output_file, xor_key)

            case 1:
                decrypt_dat_v4(input_file, output_file, xor_key, aes_key)

            case 2:
                decrypt_dat_v4(input_file, output_file, xor_key, aes_key)

        print("[+] 图片解密完成")
    except:
        print("[-] 图片解密失败, 未知错误")


if __name__ == "__main__":
    freeze_support()

    st = time.time()

    main()

    et = time.time()
    print(f"[+] 总用时: {et - st:.2f} 秒")

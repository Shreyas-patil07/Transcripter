from __future__ import annotations

import ctypes
import os
import sys
import sysconfig
from pathlib import Path


def main() -> int:
    if os.name != "nt":
        print("This CUDA DLL check is for Windows. Skipping.")
        return 0

    nvidia_root = Path(sysconfig.get_paths()["platlib"]) / "nvidia"
    packages = ("cublas", "cuda_runtime", "cuda_nvrtc", "cudnn")
    handles = []

    for package in packages:
        directory = nvidia_root / package / "bin"
        if not directory.is_dir():
            print(f"Missing NVIDIA runtime directory: {directory}", file=sys.stderr)
            return 1
        handles.append(os.add_dll_directory(str(directory)))

    required_dlls = (
        nvidia_root / "cublas" / "bin" / "cublas64_12.dll",
        nvidia_root / "cublas" / "bin" / "cublasLt64_12.dll",
        nvidia_root / "cuda_runtime" / "bin" / "cudart64_12.dll",
        nvidia_root / "cudnn" / "bin" / "cudnn64_9.dll",
    )

    try:
        for dll in required_dlls:
            if not dll.is_file():
                raise FileNotFoundError(f"Missing required DLL: {dll}")
            ctypes.WinDLL(str(dll))
            print(f"Loaded: {dll.name}")

        import ctranslate2

        device_count = ctranslate2.get_cuda_device_count()
        if device_count < 1:
            raise RuntimeError("CTranslate2 loaded CUDA libraries but detected no CUDA device.")

        compute_types = sorted(ctranslate2.get_supported_compute_types("cuda"))
        print(f"CTranslate2 version: {ctranslate2.__version__}")
        print(f"CUDA devices detected: {device_count}")
        print(f"Supported CUDA compute types: {', '.join(compute_types)}")
        print("CUDA preflight passed.")
        return 0
    except Exception as exc:
        print(f"CUDA preflight failed: {exc}", file=sys.stderr)
        print(
            "Check the NVIDIA driver and install the Microsoft Visual C++ 2015-2022 "
            "x64 Redistributable. Then rerun setup.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

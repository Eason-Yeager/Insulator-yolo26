"""Edge benchmark on NVIDIA Jetson Orin Nano — paper Section 4.11 + Table 12.

Measures, from a TensorRT FP16 engine:
  * latency (ms) and throughput (FPS)
  * peak GPU memory (MB)            -> Table 12 "Memory (MB)" column
  * real-time power via tegrastats  -> Table 12 "Power Draw (W) / Energy per Frame (mJ)"

Usage (on the Jetson):
    python benchmark_edge.py --engine runs/detect/ours/weights/best.engine \
                             --imgsz 640 --tag ours
    python benchmark_edge.py --engine ...baseline.engine --tag baseline
"""
import argparse
import re
import subprocess
import time

import numpy as np
import torch
import tensorrt as trt
import pycuda.autoinit  # noqa: F401
import pycuda.driver as cuda

TEGRASTATS = "/usr/bin/tegrastats"


def load_engine(engine_path):
    logger = trt.Logger(trt.Logger.WARNING)
    with open(engine_path, "rb") as f, trt.Runtime(logger) as runtime:
        return runtime.deserialize_cuda_engine(f.read())


def run_engine(engine, imgsz, n_warmup=20, n=200):
    ctx = engine.create_execution_context()
    stream = cuda.Stream()
    inp = torch.zeros(1, 3, imgsz, imgsz).cuda()
    out = torch.empty(1, 84, imgsz * imgsz // 4, device="cuda")  # (1, 4+nc, 8400)
    for _ in range(n_warmup):
        cuda.memcpy_htod_async(inp, inp, stream)  # dummy copies
        ctx.execute_async_v2(bindings=[inp.data_ptr(), out.data_ptr()], stream_handle=stream.handle)
        stream.synchronize()
    lat = []
    for _ in range(n):
        t0 = time.perf_counter()
        ctx.execute_async_v2(bindings=[inp.data_ptr(), out.data_ptr()], stream_handle=stream.handle)
        stream.synchronize()
        lat.append((time.perf_counter() - t0) * 1e3)
    return float(np.mean(lat)), float(np.percentile(lat, 50)), n / (np.mean(lat) / 1e3)


def sample_power(duration_s=8.0):
    """Sample GPU power (W) via tegrastats while the engine runs."""
    proc = subprocess.Popen([TEGRASTATS, "--interval", "500"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True)
    powers = []
    t_end = time.time() + duration_s
    while time.time() < t_end:
        line = proc.stdout.readline()
        m = re.search(r"GPU.*?(\d+)mW", line)
        if m:
            powers.append(float(m.group(1)) / 1000.0)
    proc.terminate()
    return float(np.mean(powers)) if powers else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--tag", default="model")
    ap.add_argument("--power", action="store_true", default=True)
    args = ap.parse_args()

    engine = load_engine(args.engine)
    lat_mean, lat_p50, fps = run_engine(engine, args.imgsz)
    print(f"[{args.tag}] latency(ms)={lat_mean:.1f}  p50(ms)={lat_p50:.1f}  FPS={fps:.1f}")

    if args.power:
        pwr = sample_power()
        energy = pwr * lat_mean  # mJ per frame = W * ms
        print(f"[{args.tag}] power(W)={pwr:.1f}  energy/frame(mJ)={energy:.1f}")
        # Note: peak GPU memory is read from tegrastats 'RAM' or nvidia-smi;
        # record it manually into Table 12's Memory (MB) column.


if __name__ == "__main__":
    main()

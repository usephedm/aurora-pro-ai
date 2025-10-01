import os
import pytest


@pytest.mark.gpu
def test_cuda_available():
    try:
        import torch
    except Exception as exc:
        pytest.skip(f"torch not available: {exc}")
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available on this runner")
    name = torch.cuda.get_device_name(0)
    assert any(x in name for x in ("4060", "NVIDIA", "GeForce"))


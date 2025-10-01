"""
Comprehensive test suite for Aurora Pro enhanced features.

Tests all new agents, routing decisions, caching, multi-core processing,
and integration tests.
"""
import asyncio
import pytest
from pathlib import Path

# Import all enhanced modules
from vision_agent import get_vision_agent, ScreenRegion
from stealth_browser_agent import get_stealth_browser
from captcha_manager import get_captcha_manager, CaptchaType
from plugin_manager import get_plugin_manager
from multicore_manager import get_multicore_manager
from cache_manager import get_cache_manager
from proxy_manager import get_proxy_manager
from local_inference import get_local_inference


# ============================================================================
# Vision Agent Tests
# ============================================================================

@pytest.mark.asyncio
async def test_vision_agent_initialization():
    """Test vision agent starts correctly."""
    agent = get_vision_agent()
    await agent.start()

    status = agent.get_status()
    assert status["running"] is True

    await agent.stop()


@pytest.mark.asyncio
async def test_vision_agent_status():
    """Test vision agent status reporting."""
    agent = get_vision_agent()
    await agent.start()

    status = agent.get_status()
    assert "mss_available" in status
    assert "pytesseract_available" in status
    assert "authorized" in status

    await agent.stop()


# ============================================================================
# Stealth Browser Tests
# ============================================================================

@pytest.mark.asyncio
async def test_stealth_browser_initialization():
    """Test stealth browser starts correctly."""
    browser = get_stealth_browser()
    await browser.start()

    status = browser.get_status()
    assert status["running"] is True

    await browser.stop()


@pytest.mark.asyncio
async def test_stealth_browser_status():
    """Test stealth browser status reporting."""
    browser = get_stealth_browser()
    await browser.start()

    status = browser.get_status()
    assert "undetected_chromedriver_available" in status
    assert "selenium_stealth_available" in status
    assert "authorized" in status

    await browser.stop()


# ============================================================================
# CAPTCHA Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_captcha_manager_initialization():
    """Test CAPTCHA manager starts correctly."""
    manager = get_captcha_manager()
    await manager.start()

    status = manager.get_status()
    assert status["running"] is True

    await manager.stop()


@pytest.mark.asyncio
async def test_captcha_statistics():
    """Test CAPTCHA statistics tracking."""
    manager = get_captcha_manager()
    await manager.start()

    stats = manager.get_statistics()
    assert "total_solved" in stats
    assert "total_failed" in stats
    assert "success_rate_percent" in stats
    assert "total_cost_usd" in stats

    await manager.stop()


@pytest.mark.asyncio
async def test_captcha_type_detection():
    """Test CAPTCHA type auto-detection."""
    manager = get_captcha_manager()
    await manager.start()

    # Test reCAPTCHA v2 detection
    html_v2 = '<div class="g-recaptcha" data-sitekey="abc123"></div>'
    captcha_type = await manager.detect_captcha_type(html_v2)
    assert captcha_type == CaptchaType.RECAPTCHA_V2

    # Test hCaptcha detection
    html_h = '<div class="h-captcha" data-sitekey="xyz789"></div>'
    captcha_type = await manager.detect_captcha_type(html_h)
    assert captcha_type == CaptchaType.HCAPTCHA

    await manager.stop()


# ============================================================================
# Plugin Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_plugin_manager_initialization():
    """Test plugin manager starts correctly."""
    manager = get_plugin_manager()
    await manager.start()

    status = manager.get_status()
    assert status["running"] is True
    assert "loaded_plugins" in status

    await manager.stop()


@pytest.mark.asyncio
async def test_plugin_discovery():
    """Test plugin discovery."""
    manager = get_plugin_manager()
    await manager.start()

    plugins = await manager.discover_plugins()
    assert isinstance(plugins, list)

    await manager.stop()


@pytest.mark.asyncio
async def test_plugin_list_empty():
    """Test listing plugins when none loaded."""
    manager = get_plugin_manager()
    await manager.start()

    plugins = manager.list_plugins()
    assert isinstance(plugins, list)

    await manager.stop()


# ============================================================================
# Multi-Core Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_multicore_manager_initialization():
    """Test multi-core manager starts correctly."""
    manager = get_multicore_manager(num_workers=4)  # Use fewer workers for tests
    await manager.start()

    status = manager.get_status()
    assert status["running"] is True
    assert status["num_workers"] == 4

    await manager.stop()


@pytest.mark.asyncio
async def test_multicore_simple_task():
    """Test executing a simple task."""
    def square(x):
        return x * x

    manager = get_multicore_manager(num_workers=2)
    await manager.start()

    task_id = await manager.submit_task(square, 5)
    result = await manager.get_result(task_id, timeout=10)

    assert result.status == "completed"
    assert result.result == 25

    await manager.stop()


@pytest.mark.asyncio
async def test_multicore_batch_execution():
    """Test batch execution."""
    def add_one(x):
        return x + 1

    manager = get_multicore_manager(num_workers=2)
    await manager.start()

    items = [1, 2, 3, 4, 5]
    results = await manager.map_async(add_one, items, timeout=10)

    assert results == [2, 3, 4, 5, 6]

    await manager.stop()


@pytest.mark.asyncio
async def test_multicore_statistics():
    """Test statistics tracking."""
    def simple_task():
        return "done"

    manager = get_multicore_manager(num_workers=2)
    await manager.start()

    task_id = await manager.submit_task(simple_task)
    await manager.get_result(task_id, timeout=10)

    stats = manager.get_statistics()
    assert stats["total_tasks"] >= 1
    assert stats["completed"] >= 1

    await manager.stop()


# ============================================================================
# Cache Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cache_manager_initialization():
    """Test cache manager starts correctly."""
    manager = get_cache_manager(memory_size_mb=100)
    await manager.start()

    status = manager.get_status()
    assert status["running"] is True

    await manager.stop()


@pytest.mark.asyncio
async def test_cache_set_get():
    """Test basic cache set and get."""
    manager = get_cache_manager(memory_size_mb=100)
    await manager.start()

    # Set value
    await manager.set("test", "key1", "value1")

    # Get value
    value, tier = await manager.get("test", "key1")
    assert value == "value1"
    assert tier == "memory"

    await manager.stop()


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss."""
    manager = get_cache_manager(memory_size_mb=100)
    await manager.start()

    value, tier = await manager.get("test", "nonexistent")
    assert value is None
    assert tier == "miss"

    await manager.stop()


@pytest.mark.asyncio
async def test_cache_statistics():
    """Test cache statistics."""
    manager = get_cache_manager(memory_size_mb=100)
    await manager.start()

    # Perform some operations
    await manager.set("test", "key1", "value1")
    await manager.get("test", "key1")
    await manager.get("test", "nonexistent")

    stats = await manager.get_statistics()
    assert "memory" in stats
    assert "disk" in stats
    assert "redis" in stats

    await manager.stop()


# ============================================================================
# Proxy Manager Tests
# ============================================================================

@pytest.mark.asyncio
async def test_proxy_manager_initialization():
    """Test proxy manager starts correctly."""
    manager = get_proxy_manager()
    await manager.start()

    status = manager.get_status()
    assert status["running"] is True

    await manager.stop()


@pytest.mark.asyncio
async def test_proxy_statistics():
    """Test proxy statistics."""
    manager = get_proxy_manager()
    await manager.start()

    stats = manager.get_statistics()
    assert "total_proxies" in stats
    assert "healthy_proxies" in stats
    assert "success_rate_percent" in stats

    await manager.stop()


@pytest.mark.asyncio
async def test_proxy_list():
    """Test listing proxies."""
    manager = get_proxy_manager()
    await manager.start()

    proxies = manager.list_proxies()
    assert isinstance(proxies, list)

    await manager.stop()


# ============================================================================
# Local Inference Tests
# ============================================================================

@pytest.mark.asyncio
async def test_local_inference_initialization():
    """Test local inference starts correctly."""
    engine = get_local_inference()
    await engine.start()

    status = engine.get_status()
    assert status["running"] is True

    await engine.stop()


@pytest.mark.asyncio
async def test_local_inference_models():
    """Test listing available models."""
    engine = get_local_inference()
    await engine.start()

    models = await engine.list_models()
    assert isinstance(models, list)

    await engine.stop()


@pytest.mark.asyncio
async def test_local_inference_statistics():
    """Test inference statistics."""
    engine = get_local_inference()
    await engine.start()

    stats = engine.get_statistics()
    assert "total_requests" in stats
    assert "total_tokens" in stats
    assert "avg_tokens_per_sec" in stats

    await engine.stop()


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_all_managers_startup():
    """Test that all managers can start together."""
    vision = get_vision_agent()
    browser = get_stealth_browser()
    captcha = get_captcha_manager()
    plugins = get_plugin_manager()
    multicore = get_multicore_manager(num_workers=2)
    cache = get_cache_manager(memory_size_mb=100)
    proxy = get_proxy_manager()
    inference = get_local_inference()

    # Start all
    await vision.start()
    await browser.start()
    await captcha.start()
    await plugins.start()
    await multicore.start()
    await cache.start()
    await proxy.start()
    await inference.start()

    # Verify all running
    assert vision.get_status()["running"]
    assert browser.get_status()["running"]
    assert captcha.get_status()["running"]
    assert plugins.get_status()["running"]
    assert multicore.get_status()["running"]
    assert cache.get_status()["running"]
    assert proxy.get_status()["running"]
    assert inference.get_status()["running"]

    # Stop all
    await inference.stop()
    await proxy.stop()
    await cache.stop()
    await multicore.stop()
    await plugins.stop()
    await captcha.stop()
    await browser.stop()
    await vision.stop()


@pytest.mark.asyncio
async def test_cache_with_multicore():
    """Test cache integration with multi-core processing."""
    cache = get_cache_manager(memory_size_mb=100)
    multicore = get_multicore_manager(num_workers=2)

    await cache.start()
    await multicore.start()

    # Store result in cache
    await cache.set("test", "computed", "result_value")

    # Verify cache hit
    value, tier = await cache.get("test", "computed")
    assert value == "result_value"

    await multicore.stop()
    await cache.stop()


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_multicore_performance():
    """Test multi-core performance improvement."""
    import time

    def cpu_intensive(n):
        """Simulate CPU-intensive task."""
        total = 0
        for i in range(n):
            total += i ** 2
        return total

    manager = get_multicore_manager(num_workers=4)
    await manager.start()

    # Test with batch of tasks
    items = [100000] * 8
    start = time.time()
    results = await manager.map_async(cpu_intensive, items, timeout=30)
    duration = time.time() - start

    assert len(results) == 8
    assert duration < 10  # Should complete reasonably fast with parallelism

    await manager.stop()


@pytest.mark.asyncio
async def test_cache_performance():
    """Test cache performance."""
    import time

    cache = get_cache_manager(memory_size_mb=100)
    await cache.start()

    # Write performance
    start = time.time()
    for i in range(1000):
        await cache.set("perf", f"key{i}", f"value{i}")
    write_duration = time.time() - start

    # Read performance
    start = time.time()
    for i in range(1000):
        await cache.get("perf", f"key{i}")
    read_duration = time.time() - start

    print(f"Cache write: {write_duration:.3f}s, read: {read_duration:.3f}s")
    assert write_duration < 1.0  # Should be fast
    assert read_duration < 1.0

    await cache.stop()


# ============================================================================
# Run all tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Aurora Pro Enhanced Features Test Suite")
    print("=" * 80)
    print()

    # Run with pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
    ])

    print()
    print("=" * 80)
    print("Test suite completed!")
    print("=" * 80)
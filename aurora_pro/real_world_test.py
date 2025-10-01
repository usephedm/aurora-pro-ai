#!/usr/bin/env python3
"""
Real-world Aurora Pro Testing Script
Tests actual functionality with detailed output
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class AuroraTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = []

    def print_header(self, text):
        print(f"\n{'='*70}")
        print(f"  {text}")
        print('='*70)

    def test(self, name: str, func):
        """Run a single test"""
        print(f"\n🧪 Testing: {name}")
        try:
            result = func()
            if result:
                print(f"   ✅ PASSED")
                self.passed += 1
                self.tests_run.append((name, "PASSED", None))
                return True
            else:
                print(f"   ❌ FAILED: Test returned False")
                self.failed += 1
                self.tests_run.append((name, "FAILED", "Returned False"))
                return False
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            self.failed += 1
            self.tests_run.append((name, "FAILED", str(e)))
            return False

    def summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        print(f"\n  Total Tests: {self.passed + self.failed}")
        print(f"  ✅ Passed: {self.passed}")
        print(f"  ❌ Failed: {self.failed}")
        print(f"  Success Rate: {(self.passed/(self.passed+self.failed)*100):.1f}%")

        if self.failed > 0:
            print(f"\n  Failed Tests:")
            for name, status, error in self.tests_run:
                if status == "FAILED":
                    print(f"    • {name}")
                    if error:
                        print(f"      Error: {error}")

        print("\n" + "="*70 + "\n")

        return self.failed == 0

def test_api_connection():
    """Test basic API connectivity"""
    try:
        r = requests.get(f"{BASE_URL}/health/status", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            print(f"   Status code: {r.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to {BASE_URL}")
        print(f"   Is Aurora Pro running? Start with: ./run_aurora.sh")
        return False

def test_router_status():
    """Test enhanced router"""
    r = requests.get(f"{BASE_URL}/router/status", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Agents configured: {len(data.get('agents', {}))}")
        for agent_name, info in data.get('agents', {}).items():
            status = "🟢" if info.get('available') else "🔴"
            print(f"     {status} {agent_name}: {info.get('total_tasks', 0)} tasks")
        return True
    return False

def test_cache_manager():
    """Test cache functionality"""
    r = requests.get(f"{BASE_URL}/cache/stats", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Cache tiers: {len(data.get('tiers', {}))}")
        for tier, stats in data.get('tiers', {}).items():
            print(f"     {tier}: {stats.get('hits', 0)} hits, {stats.get('misses', 0)} misses")
        return True
    return False

def test_vision_agent_status():
    """Test vision agent (might be disabled)"""
    r = requests.get(f"{BASE_URL}/vision/status", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Vision enabled: {data.get('enabled', False)}")
        print(f"   Tesseract available: {data.get('tesseract_available', False)}")
        return True
    elif r.status_code == 403:
        print(f"   Vision agent disabled (expected if not enabled in config)")
        return True  # This is OK
    return False

def test_multicore_stats():
    """Test multi-core manager"""
    r = requests.get(f"{BASE_URL}/multicore/stats", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Workers: {data.get('worker_count', 0)}")
        print(f"   Queue size: {data.get('queue_size', 0)}")
        print(f"   Tasks processed: {data.get('total_tasks', 0)}")
        return True
    return False

def test_cli_agent_status():
    """Test CLI agent status"""
    r = requests.get(f"{BASE_URL}/cli/status", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Claude agent available: {data.get('claude', {}).get('available', False)}")
        print(f"   Codex agent available: {data.get('codex', {}).get('available', False)}")
        return True
    return False

def test_input_agent_status():
    """Test input agent"""
    r = requests.get(f"{BASE_URL}/input/status", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Queue size: {data.get('queue_size', 0)}")
        print(f"   Tasks processed: {len(data.get('recent_tasks', []))}")
        return True
    return False

def test_heartbeat():
    """Test heartbeat monitoring"""
    r = requests.get(f"{BASE_URL}/health/heartbeat", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Running: {data.get('running', False)}")
        print(f"   Uptime: {data.get('uptime_seconds', 0):.1f}s")
        print(f"   Error counts: {data.get('error_counts', {})}")
        return True
    return False

def test_metrics():
    """Test Prometheus metrics"""
    r = requests.get(f"{BASE_URL}/metrics", timeout=5)
    if r.status_code == 200:
        lines = r.text.split('\n')
        metric_count = len([l for l in lines if l and not l.startswith('#')])
        print(f"   Metrics exposed: {metric_count} values")
        return True
    return False

def test_plugin_list():
    """Test plugin system"""
    r = requests.get(f"{BASE_URL}/plugins/list", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Loaded plugins: {len(data.get('loaded_plugins', []))}")
        return True
    elif r.status_code == 403:
        print(f"   Plugin system disabled (expected if not enabled)")
        return True
    return False

def test_inference_status():
    """Test local inference engine"""
    r = requests.get(f"{BASE_URL}/inference/status", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   Ollama running: {data.get('ollama_running', False)}")
        print(f"   Models available: {len(data.get('models', []))}")
        return True
    elif r.status_code == 403:
        print(f"   Local inference disabled (expected if not enabled)")
        return True
    return False

def main():
    tester = AuroraTest()

    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              AURORA PRO - REAL WORLD TEST SUITE                          ║
║                                                                           ║
║              Testing actual functionality in production                   ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    # Critical tests
    tester.print_header("CRITICAL TESTS (Must Pass)")
    tester.test("API Connection", test_api_connection)

    if tester.failed > 0:
        print("\n⚠️  API is not running! Start Aurora Pro first:")
        print("   cd /root/aurora_pro")
        print("   ./run_aurora.sh")
        return False

    # Core functionality tests
    tester.print_header("CORE FUNCTIONALITY TESTS")
    tester.test("Health Status", test_api_connection)
    tester.test("Enhanced Router", test_router_status)
    tester.test("Cache Manager", test_cache_manager)
    tester.test("Multi-Core Manager", test_multicore_stats)
    tester.test("CLI Agent Status", test_cli_agent_status)
    tester.test("Input Agent Status", test_input_agent_status)
    tester.test("Heartbeat Monitor", test_heartbeat)

    # Monitoring tests
    tester.print_header("MONITORING & METRICS TESTS")
    tester.test("Prometheus Metrics", test_metrics)

    # Optional features (may be disabled)
    tester.print_header("OPTIONAL FEATURES (May be disabled)")
    tester.test("Vision Agent", test_vision_agent_status)
    tester.test("Plugin System", test_plugin_list)
    tester.test("Local Inference", test_inference_status)

    # Summary
    success = tester.summary()

    if success:
        print("🎉 All tests passed! Aurora Pro is fully operational.\n")
        return True
    else:
        print("⚠️  Some tests failed. Review errors above.\n")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
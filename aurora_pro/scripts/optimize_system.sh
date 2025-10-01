#!/bin/bash
# System Optimization Script for Aurora Pro on 32-core i9-13900HX
# Optimizes CPU governor, swap, I/O, and network settings for maximum performance

set -e

echo "========================================"
echo "Aurora Pro System Optimization Script"
echo "Target: 32-core i9-13900HX, 62GB RAM"
echo "OS: Kali Linux"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    echo "Please run: sudo $0"
    exit 1
fi

echo "[1/8] Setting CPU governor to performance mode..."
# Set all CPU cores to performance governor for maximum throughput
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    if [ -f "$cpu" ]; then
        echo "performance" > "$cpu"
    fi
done

# Disable CPU frequency scaling turbo boost throttling
if [ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
    echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo
    echo "  - Intel Turbo Boost enabled"
fi

echo "  - CPU governor set to performance mode on all 32 cores"

echo ""
echo "[2/8] Configuring swap..."
# With 62GB RAM, reduce swap usage (swappiness=10 is good for high-RAM systems)
sysctl -w vm.swappiness=10
sysctl -w vm.vfs_cache_pressure=50
echo "  - Swappiness set to 10 (minimal swap usage with 62GB RAM)"

echo ""
echo "[3/8] Optimizing I/O scheduler..."
# Use mq-deadline for SSDs or none for NVMe (best for random I/O)
for disk in /sys/block/sd*/queue/scheduler; do
    if [ -f "$disk" ]; then
        echo "mq-deadline" > "$disk" 2>/dev/null || echo "none" > "$disk" 2>/dev/null || true
    fi
done

for disk in /sys/block/nvme*/queue/scheduler; do
    if [ -f "$disk" ]; then
        echo "none" > "$disk" 2>/dev/null || true
    fi
done
echo "  - I/O scheduler optimized for SSD/NVMe"

echo ""
echo "[4/8] Tuning filesystem mount options..."
# Check if /tmp is mounted
if mountpoint -q /tmp; then
    echo "  - /tmp already mounted"
else
    # Mount /tmp as tmpfs for faster temporary file operations
    mount -t tmpfs -o size=8G,mode=1777 tmpfs /tmp 2>/dev/null || true
    echo "  - /tmp mounted as tmpfs (8GB)"
fi

echo ""
echo "[5/8] Network stack optimization..."
# Increase network buffer sizes for high-throughput operations
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 67108864"
sysctl -w net.ipv4.tcp_wmem="4096 65536 67108864"
sysctl -w net.core.netdev_max_backlog=5000
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Enable TCP Fast Open
sysctl -w net.ipv4.tcp_fastopen=3

echo "  - Network buffers increased for high throughput"
echo "  - TCP BBR congestion control enabled"
echo "  - TCP Fast Open enabled"

echo ""
echo "[6/8] Memory management tuning..."
# Optimize for high-memory system
sysctl -w vm.dirty_ratio=15
sysctl -w vm.dirty_background_ratio=5
sysctl -w vm.min_free_kbytes=1048576  # 1GB minimum free

# Disable transparent huge pages (can cause latency spikes)
echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
echo never > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true

echo "  - Memory management optimized for 62GB RAM"
echo "  - Transparent huge pages disabled"

echo ""
echo "[7/8] Process scheduler optimization..."
# Optimize scheduler for multi-core throughput
sysctl -w kernel.sched_migration_cost_ns=5000000
sysctl -w kernel.sched_autogroup_enabled=0

echo "  - Scheduler optimized for 32-core workloads"

echo ""
echo "[8/8] Security and limits..."
# Increase file descriptor limits for high concurrency
ulimit -n 65536 2>/dev/null || true

# Set in /etc/security/limits.conf for persistence
if ! grep -q "aurora-limits" /etc/security/limits.conf 2>/dev/null; then
    echo "# aurora-limits" >> /etc/security/limits.conf
    echo "* soft nofile 65536" >> /etc/security/limits.conf
    echo "* hard nofile 65536" >> /etc/security/limits.conf
    echo "  - File descriptor limits increased to 65536"
else
    echo "  - File descriptor limits already configured"
fi

# Increase max user processes
sysctl -w kernel.pid_max=4194304

echo ""
echo "========================================"
echo "Optimization Complete!"
echo "========================================"
echo ""
echo "Current system configuration:"
echo "  - CPU Governor: performance (all 32 cores)"
echo "  - Swappiness: 10"
echo "  - Network: BBR congestion control, 128MB buffers"
echo "  - Memory: Optimized for 62GB RAM"
echo "  - File descriptors: 65536"
echo ""
echo "To make these changes persistent across reboots:"
echo "1. Add this script to /etc/rc.local or systemd service"
echo "2. Or add sysctl settings to /etc/sysctl.d/99-aurora.conf"
echo ""
echo "Monitoring commands:"
echo "  - CPU frequency: watch -n1 'grep MHz /proc/cpuinfo'"
echo "  - System load: htop or top"
echo "  - Network: iftop"
echo "  - I/O: iotop"
echo ""
echo "Aurora Pro is now optimized for maximum performance!"
echo "========================================"
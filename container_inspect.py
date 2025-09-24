import math
import os


def get_cgroup_cpu_count():
    try:
        quota = int(open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read())
        period = int(open("/sys/fs/cgroup/cpu/cpu.cfs_period_us").read())
        if quota > 0 and period > 0:
            return math.ceil(quota / period)
    except Exception:
        pass

    try:
        cpus = open("/sys/fs/cgroup/cpuset/cpuset.cpus").read().strip()
        if cpus:
            count = 0
            for part in cpus.split(","):
                if "-" in part:
                    a, b = map(int, part.split("-"))
                    count += b - a + 1
                else:
                    count += 1
            return count
    except Exception:
        pass

    return os.cpu_count()


if __name__ == "__main__":
    print("Container visible CPUs:", get_cgroup_cpu_count())

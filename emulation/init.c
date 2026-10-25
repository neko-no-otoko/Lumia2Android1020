/* Original synthetic ARM userspace smoke tests. No handset code or firmware.
 * Linux syscall and Binder UAPI headers come from pinned Debian cross headers.
 * Binder ABI tests are not Android framework/HAL or Lumia hardware tests.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/android/binder.h>
#include <linux/android/binderfs.h>
#include <linux/time_types.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/timerfd.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define REQUIRE(value) do { if (!(value)) { printf("DETAIL line=%d errno=%d\n", __LINE__, errno); return -1; } } while (0)

static int identity(void)
{
    struct utsname info;
    REQUIRE(getpid() == 1 && sizeof(void *) == 4);
    REQUIRE(uname(&info) == 0 && strcmp(info.machine, "armv7l") == 0);
    REQUIRE(strncmp(info.release, "6.6.0", 5) == 0);
    printf("GUEST %s %s pid=%d word_bits=%zu\n", info.release, info.machine, getpid(), sizeof(void *)*8);
    return 0;
}

static int mounts(void)
{
    mkdir("/proc", 0755); mkdir("/sys", 0755); mkdir("/tmp", 0755);
    REQUIRE(mount("proc", "/proc", "proc", MS_NOSUID|MS_NODEV|MS_NOEXEC, NULL) == 0);
    REQUIRE(mount("sysfs", "/sys", "sysfs", MS_NOSUID|MS_NODEV|MS_NOEXEC, NULL) == 0);
    REQUIRE(mount("tmpfs", "/tmp", "tmpfs", MS_NOSUID|MS_NODEV, "size=8m") == 0);
    int fd = open("/tmp/synthetic", O_CREAT|O_RDWR|O_EXCL, 0600);
    REQUIRE(fd >= 0 && write(fd, "ram-only", 8) == 8);
    REQUIRE(lseek(fd, 0, SEEK_SET) == 0);
    char buf[8]; REQUIRE(read(fd, buf, 8) == 8 && memcmp(buf, "ram-only", 8) == 0);
    close(fd); REQUIRE(unlink("/tmp/synthetic") == 0);
    return 0;
}

static int memory(void)
{
    long page = sysconf(_SC_PAGESIZE);
    unsigned char *p = mmap(NULL, 4*page, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    REQUIRE(p != MAP_FAILED);
    for (long i = 0; i < 4*page; i++) REQUIRE(p[i] == 0);
    memset(p, 0x5a, 4*page);
    REQUIRE(mprotect(p, page, PROT_READ) == 0);
    pid_t child = fork(); REQUIRE(child >= 0);
    if (!child) { p[0] = 1; _exit(9); }
    int status; REQUIRE(waitpid(child, &status, 0) == child);
    REQUIRE(WIFSIGNALED(status) && WTERMSIG(status) == SIGSEGV && p[0] == 0x5a);
    REQUIRE(mprotect(p, page, PROT_READ|PROT_WRITE) == 0 && munmap(p, 4*page) == 0);
    return 0;
}

static int fork_pipe(void)
{
    volatile int cow = 7;
    int pipefd[2]; REQUIRE(pipe2(pipefd, O_CLOEXEC) == 0);
    pid_t child = fork(); REQUIRE(child >= 0);
    if (!child) {
        close(pipefd[0]); cow = 42;
        int value = cow;
        _exit(write(pipefd[1], &value, sizeof(value)) == sizeof(value) ? 0 : 1);
    }
    close(pipefd[1]); int value = 0, status;
    REQUIRE(read(pipefd[0], &value, sizeof(value)) == sizeof(value));
    REQUIRE(waitpid(child, &status, 0) == child && WIFEXITED(status) && WEXITSTATUS(status) == 0);
    close(pipefd[0]); REQUIRE(value == 42 && cow == 7);
    return 0;
}

static int smp_affinity(void)
{
    cpu_set_t cpus;
    CPU_ZERO(&cpus); CPU_SET(1, &cpus);
    REQUIRE(sched_setaffinity(0, sizeof(cpus), &cpus) == 0 && sched_getcpu() == 1);
    CPU_SET(0, &cpus); REQUIRE(sched_setaffinity(0, sizeof(cpus), &cpus) == 0);
    return 0;
}

static int clock_epoll(void)
{
    struct timespec before, after;
    REQUIRE(clock_gettime(CLOCK_MONOTONIC, &before) == 0);
    int timer = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC);
    int epoll = epoll_create1(EPOLL_CLOEXEC); REQUIRE(timer >= 0 && epoll >= 0);
    struct itimerspec delay = {.it_value = {.tv_nsec = 20000000}};
    struct epoll_event event = {.events = EPOLLIN, .data.fd = timer};
    REQUIRE(timerfd_settime(timer, 0, &delay, NULL) == 0);
    REQUIRE(epoll_ctl(epoll, EPOLL_CTL_ADD, timer, &event) == 0);
    REQUIRE(epoll_wait(epoll, &event, 1, 2000) == 1 && event.data.fd == timer);
    uint64_t count; REQUIRE(read(timer, &count, sizeof(count)) == sizeof(count) && count >= 1);
    REQUIRE(clock_gettime(CLOCK_MONOTONIC, &after) == 0);
    REQUIRE(after.tv_sec > before.tv_sec || (after.tv_sec == before.tv_sec && after.tv_nsec > before.tv_nsec));
    /* Exercise the modern time64 ABI as well as glibc's default time32 call. */
    struct __kernel_itimerspec delay64 = {.it_value = {.tv_nsec = 20000000}};
    REQUIRE(syscall(SYS_timerfd_settime64, timer, 0, &delay64, NULL) == 0);
    REQUIRE(epoll_wait(epoll, &event, 1, 2000) == 1);
    REQUIRE(read(timer, &count, sizeof(count)) == sizeof(count) && count >= 1);
    close(timer); close(epoll); return 0;
}

static int namespace(void)
{
    struct utsname before, after; REQUIRE(uname(&before) == 0);
    pid_t child = fork(); REQUIRE(child >= 0);
    if (!child) _exit(unshare(CLONE_NEWUTS) == 0 && sethostname("synthetic-guest", 15) == 0 ? 0 : 1);
    int status; REQUIRE(waitpid(child, &status, 0) == child && WIFEXITED(status) && WEXITSTATUS(status) == 0);
    REQUIRE(uname(&after) == 0 && strcmp(before.nodename, after.nodename) == 0);
    return 0;
}

static int binder_abi(void)
{
    mkdir("/dev/binderfs", 0755);
    REQUIRE(mount("binder", "/dev/binderfs", "binder", 0, NULL) == 0);
    int ctl = open("/dev/binderfs/binder-control", O_RDWR|O_CLOEXEC); REQUIRE(ctl >= 0);
    struct binderfs_device device = {.name = "synthetic"};
    REQUIRE(ioctl(ctl, BINDER_CTL_ADD, &device) == 0);
    int fd = open("/dev/binderfs/synthetic", O_RDWR|O_CLOEXEC); REQUIRE(fd >= 0);
    struct binder_version version;
    REQUIRE(ioctl(fd, BINDER_VERSION, &version) == 0 && version.protocol_version == BINDER_CURRENT_PROTOCOL_VERSION);
    printf("BINDER protocol=%d device=%u:%u\n", version.protocol_version, device.major, device.minor);
    /* Linux6.6 maps failed BINDER_VERSION put_user to EINVAL, not EFAULT. */
    errno = 0; REQUIRE(ioctl(fd, BINDER_VERSION, NULL) == -1 && errno == EINVAL);
    errno = 0; REQUIRE(ioctl(fd, 0xdeadbeefUL, NULL) == -1 && errno == EINVAL);
    void *map = mmap(NULL, 8192, PROT_READ, MAP_PRIVATE, fd, 0); REQUIRE(map != MAP_FAILED);
    uint32_t invalid_command = 0;
    struct binder_write_read exchange = {.write_size = sizeof(invalid_command), .write_buffer = (uintptr_t)&invalid_command};
    errno = 0; REQUIRE(ioctl(fd, BINDER_WRITE_READ, &exchange) == -1 && errno == EINVAL);
    exchange.write_buffer = 1; exchange.write_consumed = 0;
    errno = 0; REQUIRE(ioctl(fd, BINDER_WRITE_READ, &exchange) == -1 && errno == EFAULT);
    REQUIRE(munmap(map, 8192) == 0);
    close(fd); close(ctl); REQUIRE(unlink("/dev/binderfs/synthetic") == 0);
    return 0;
}

int main(void)
{
    mkdir("/dev", 0755);
    if (mount("devtmpfs", "/dev", "devtmpfs", MS_NOSUID, NULL) != 0) return 1;
    int console = open("/dev/console", O_RDWR);
    if (console < 0) return 2;
    dup2(console, 0); dup2(console, 1); dup2(console, 2);
    if (console > 2) close(console);
    setvbuf(stdout, NULL, _IONBF, 0);
    struct { const char *name; int (*run)(void); } tests[] = {
        {"identity", identity}, {"mounts", mounts}, {"memory", memory}, {"fork_pipe", fork_pipe},
        {"smp_affinity", smp_affinity}, {"clock_epoll", clock_epoll}, {"namespace", namespace}, {"binder_abi", binder_abi},
    };
    int failures = 0;
    for (size_t i = 0; i < sizeof(tests)/sizeof(tests[0]); i++) {
        int result = tests[i].run(); failures += result != 0;
        printf("%s %s\n", result ? "SMOKE_FAIL" : "SMOKE_OK", tests[i].name);
    }
    if (!failures) printf("SMOKE_COMPLETE\n");
    else printf("SMOKE_FAILURES %d\n", failures);
    sync(); reboot(RB_POWER_OFF);
    for (;;) pause();
}

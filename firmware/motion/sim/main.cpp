// Host simulator: the real controller core on a pseudo-terminal, with FakeHal physics.
// Prints the pty path on stdout, then serves the §3 protocol on it until killed.
//   ./sim/build/fwsim [--speed N] [--undocked]
// Lets the Pi application's SerialMotion client be tested against the firmware logic.
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#include <chrono>
#include <string>
#include <thread>

#include "controller.h"
#include "fake_hal.h"

using namespace rbg3;

class PtyHal : public FakeHal {
 public:
  int fd = -1;
  void writeLine(const char* line) override {
    std::string s = std::string(line) + "\n";
    ssize_t n = ::write(fd, s.data(), s.size());
    (void)n;
  }
};

int main(int argc, char** argv) {
  double speed = 1.0;
  bool docked = true;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--speed") && i + 1 < argc) speed = atof(argv[++i]);
    if (!strcmp(argv[i], "--undocked")) docked = false;
  }
  int master = posix_openpt(O_RDWR | O_NOCTTY);
  if (master < 0 || grantpt(master) || unlockpt(master)) {
    perror("pty");
    return 1;
  }
  termios t;
  tcgetattr(master, &t);
  cfmakeraw(&t);
  tcsetattr(master, TCSANOW, &t);
  fcntl(master, F_SETFL, O_NONBLOCK);
  printf("%s\n", ptsname(master));
  fflush(stdout);

  PtyHal hal;
  hal.fd = master;
  hal.nose_fixed = docked;
  hal.dock_v = docked ? 24.0f : 0.0f;
  Controller c(hal);
  c.begin();

  using clock = std::chrono::steady_clock;
  auto last = clock::now();
  double carry_ms = 0;
  char buf[256];
  for (;;) {
    ssize_t n = read(master, buf, sizeof buf);
    for (ssize_t i = 0; i < n; i++) c.feed(buf[i]);
    auto now = clock::now();
    carry_ms += std::chrono::duration<double, std::milli>(now - last).count() * speed;
    last = now;
    while (carry_ms >= 1.0) {  // 1 ms simulation steps
      hal.tick(1);
      carry_ms -= 1.0;
      c.update();
    }
    std::this_thread::sleep_for(std::chrono::microseconds(500));
  }
}

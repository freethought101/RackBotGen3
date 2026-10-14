// Host unit tests for the motion controller core: pio test -e native
#include <stdio.h>
#include <string.h>
#include <unity.h>

#include <string>
#include <vector>

#include "../../sim/fake_hal.h"
#include "controller.h"

using namespace rbg3;

struct Rig {
  FakeHal hal;
  Controller c{hal};

  Rig() {
    c.begin();
    run(300);  // VMOT present: drivers configured after the settle time
  }
  void run(uint32_t ms) {
    for (uint32_t t = 0; t < ms; t += 5) {
      hal.tick(5);
      c.update();
    }
  }
  // Send a request and return the lines written in response (telemetry filtered out).
  std::vector<std::string> send(const char* line) {
    size_t mark = hal.out.size();
    char buf[kMaxLine + 1];
    snprintf(buf, sizeof buf, "%s", line);
    c.handleLine(buf);
    return since(mark);
  }
  std::vector<std::string> since(size_t mark) {
    std::vector<std::string> r;
    for (size_t i = mark; i < hal.out.size(); i++)
      if (hal.out[i].rfind("TEL ", 0) != 0) r.push_back(hal.out[i]);
    return r;
  }
  // Run until a line starting with `prefix` appears (or timeout). Returns it, "" on timeout.
  std::string waitFor(const char* prefix, uint32_t timeout_ms = 60000) {
    size_t mark = hal.out.size();
    for (uint32_t t = 0; t < timeout_ms; t += 5) {
      hal.tick(5);
      c.update();
      for (size_t i = mark; i < hal.out.size(); i++)
        if (hal.out[i].rfind(prefix, 0) == 0) return hal.out[i];
    }
    return "";
  }
  bool has(const char* line) {
    for (auto& l : hal.out)
      if (l == line) return true;
    return false;
  }
  void ready() {  // enabled and homed, docked
    hal.nose_fixed = true;
    TEST_ASSERT_EQUAL_STRING("1 OK", send("1 ENABLE 1")[0].c_str());
    send("2 HOME Y");
    TEST_ASSERT_EQUAL_STRING("2 DONE", waitFor("2 ").c_str());
    send("3 HOME Z");
    TEST_ASSERT_EQUAL_STRING("3 DONE", waitFor("3 ").c_str());
  }
};

#define ASSERT_REPLY(expected, lines)                       \
  do {                                                      \
    std::vector<std::string> got_ = (lines);                \
    TEST_ASSERT_TRUE_MESSAGE(!got_.empty(), "no reply");    \
    TEST_ASSERT_EQUAL_STRING(expected, got_[0].c_str());    \
  } while (0)

void setUp() {}
void tearDown() {}

// --- protocol -----------------------------------------------------------------------------------

void test_parse_request() {
  char line[] = "12 Z 194.5 15";
  Request r;
  TEST_ASSERT_TRUE(parseRequest(line, r));
  TEST_ASSERT_EQUAL_UINT16(12, r.seq);
  TEST_ASSERT_EQUAL_STRING("Z", r.cmd);
  TEST_ASSERT_EQUAL_INT(2, r.argc);
  float v;
  TEST_ASSERT_TRUE(parseNumber(r.argv[0], v));
  TEST_ASSERT_EQUAL_FLOAT(194.5f, v);
  char bad1[] = "0 PING", bad2[] = "PING", bad3[] = "70000 PING", bad4[] = "1 A 1 2 3 4 5";
  TEST_ASSERT_FALSE(parseRequest(bad1, r));
  TEST_ASSERT_FALSE(parseRequest(bad2, r));
  TEST_ASSERT_FALSE(parseRequest(bad3, r));
  TEST_ASSERT_FALSE(parseRequest(bad4, r));
  TEST_ASSERT_FALSE(parseNumber("12x", v));
  TEST_ASSERT_FALSE(parseNumber("", v));
}

void test_line_buffer_drops_overlong_lines() {
  LineBuffer lb;
  for (int i = 0; i < 200; i++) TEST_ASSERT_FALSE(lb.feed('x'));
  TEST_ASSERT_FALSE(lb.feed('\n'));  // overflowed line is discarded
  const char* ok = "1 PING\r\n";
  bool got = false;
  for (const char* p = ok; *p; p++) got = lb.feed(*p);
  TEST_ASSERT_TRUE(got);
  TEST_ASSERT_EQUAL_STRING("1 PING", lb.line());
}

void test_boot_and_ping() {
  Rig r;
  TEST_ASSERT_TRUE(r.has("EVT BOOT RBG3-FW 0.1.0"));
  TEST_ASSERT_TRUE(r.has("EVT ESTOP_CLEAR"));
  TEST_ASSERT_TRUE(r.c.driversOk());
  ASSERT_REPLY("5 OK RBG3-FW 0.1.0", r.send("5 PING"));
  ASSERT_REPLY("6 ERR E_ARG unknown command", r.send("6 FLY"));
  ASSERT_REPLY("EVT BADLINE", r.send("hello"));
  ASSERT_REPLY("7 ERR E_INTERLOCK drivers disabled", r.send("7 Z 150"));
}

void test_boot_without_vmot() {
  FakeHal hal;
  hal.vmot_v = 0;
  Controller c(hal);
  c.begin();
  for (int i = 0; i < 200; i++) {
    hal.tick(5);
    c.update();
  }
  TEST_ASSERT_EQUAL_STRING("EVT ESTOP", hal.out[1].c_str());
  TEST_ASSERT_FALSE(c.driversOk());
  char line[] = "1 ENABLE 1";
  c.handleLine(line);
  TEST_ASSERT_EQUAL_STRING("1 ERR E_ESTOP drivers not configured", hal.out.back().c_str());
}

// --- homing -------------------------------------------------------------------------------------

void test_homing_finds_switches() {
  Rig r;
  r.hal.nose_fixed = true;
  r.send("1 ENABLE 1");
  ASSERT_REPLY("2 ERR E_NOT_HOMED home Y first", r.send("2 HOME Z"));
  ASSERT_REPLY("3 OK", r.send("3 HOME Y"));
  TEST_ASSERT_EQUAL_STRING("3 DONE", r.waitFor("3 ").c_str());
  TEST_ASSERT_TRUE(r.c.homed(AX_Y));
  TEST_ASSERT_FLOAT_WITHIN(0.05f, 0.0f, r.c.mm(AX_Y));
  TEST_ASSERT_FLOAT_WITHIN(0.05, 0.0, r.hal.physMm(AX_Y));
  r.send("4 HOME Z");
  TEST_ASSERT_EQUAL_STRING("4 DONE", r.waitFor("4 ").c_str());
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 100.0f, r.c.mm(AX_Z));  // home switch = Z 100
}

void test_homing_with_broken_switch_wire_fails_safe() {
  Rig r;
  r.hal.home_wire_broken = true;  // NC input reads "pressed": must not drive into the end stop
  r.send("1 ENABLE 1");
  r.send("2 HOME Y");
  TEST_ASSERT_EQUAL_STRING("2 FAIL E_LIMIT", r.waitFor("2 ").c_str());
  TEST_ASSERT_FALSE(r.c.homed(AX_Y));
}

void test_homing_without_switch_gives_up() {
  Rig r;
  r.hal.ax[AX_Y].phys = 1e9;  // switch unreachable
  r.send("1 ENABLE 1");
  r.send("2 HOME Y");
  TEST_ASSERT_EQUAL_STRING("2 FAIL E_LIMIT", r.waitFor("2 ", 120000).c_str());
}

// --- interlocks ---------------------------------------------------------------------------------

void test_axis_interlocks() {
  Rig r;
  r.ready();
  ASSERT_REPLY("10 ERR E_LIMIT", r.send("10 Z 50"));
  ASSERT_REPLY("11 ERR E_LIMIT", r.send("11 Y 181"));
  r.send("12 Y 60");
  ASSERT_REPLY("13 ERR E_BUSY", r.send("13 Z 150"));
  TEST_ASSERT_EQUAL_STRING("12 DONE", r.waitFor("12 ").c_str());
  ASSERT_REPLY("14 ERR E_INTERLOCK Y > 2", r.send("14 Z 150"));
  ASSERT_REPLY("15 ERR E_INTERLOCK Y mid-stroke", r.send("15 FINGER A ENGAGE"));
  ASSERT_REPLY("16 ERR E_INTERLOCK Y or Z not in travel pose", r.send("16 DRIVE 100"));
  ASSERT_REPLY("17 ERR E_INTERLOCK Y or Z not in travel pose", r.send("17 VEL 50 0"));
  r.send("18 Y 177");
  r.waitFor("18 ");
  ASSERT_REPLY("19 OK", r.send("19 FINGER A ENGAGE"));  // allowed at Y_PULL
  TEST_ASSERT_EQUAL_STRING("19 DONE", r.waitFor("19 ").c_str());
  TEST_ASSERT_EQUAL_FLOAT(90.0f, r.hal.servo_deg[0]);
  r.send("20 Y 0");
  r.waitFor("20 ");
  r.send("21 Z 230");
  r.waitFor("21 ");
  ASSERT_REPLY("22 ERR E_INTERLOCK Y or Z not in travel pose", r.send("22 TURN 90"));
}

void test_y_needs_dock_unless_bench() {
  Rig r;
  r.ready();
  r.hal.nose_fixed = false;
  r.run(10);
  ASSERT_REPLY("10 ERR E_INTERLOCK not docked", r.send("10 Y 50"));
  ASSERT_REPLY("11 OK", r.send("11 Y 1"));  // retracting / small moves stay allowed
  r.waitFor("11 ");
  ASSERT_REPLY("12 OK", r.send("12 CFG bench 1"));
  ASSERT_REPLY("13 OK", r.send("13 Y 50"));
}

void test_z_move_and_speed_clamp() {
  Rig r;
  r.ready();
  ASSERT_REPLY("10 OK", r.send("10 Z 194 999"));  // speed clamped to v_z = 15 mm/s
  uint32_t t0 = r.hal.now;
  TEST_ASSERT_EQUAL_STRING("10 DONE", r.waitFor("10 ").c_str());
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 194.0f, r.c.mm(AX_Z));
  TEST_ASSERT_UINT32_WITHIN(200, 6267, r.hal.now - t0);  // 94 mm at 15 mm/s
}

// --- driving ------------------------------------------------------------------------------------

void test_turn_direction_and_arc() {
  Rig r;
  r.ready();
  r.send("10 TURN 90");
  TEST_ASSERT_EQUAL_STRING("10 DONE", r.waitFor("10 ").c_str());
  float arc = 274.0f / 2 * 3.14159265f / 2;
  TEST_ASSERT_FLOAT_WITHIN(0.2f, -arc, r.c.mm(AX_L));
  TEST_ASSERT_FLOAT_WITHIN(0.2f, arc, r.c.mm(AX_R));
}

void test_vel_watchdog() {
  Rig r;
  r.ready();
  ASSERT_REPLY("10 OK", r.send("10 VEL 100 0"));
  TEST_ASSERT_TRUE(r.c.busy());
  ASSERT_REPLY("11 ERR E_BUSY", r.send("11 DRIVE 10"));
  r.run(250);
  ASSERT_REPLY("12 OK", r.send("12 VEL 100 0"));  // refresh
  r.run(250);
  TEST_ASSERT_TRUE(r.hal.running(AX_L));
  r.run(100);
  TEST_ASSERT_FALSE(r.hal.running(AX_L));
  TEST_ASSERT_FALSE(r.c.busy());
  TEST_ASSERT_FLOAT_WITHIN(3.0f, 55.0f, r.c.mm(AX_L));  // 0.55 s at 100 mm/s
}

void test_dock_until_nose() {
  Rig r;
  r.ready();
  r.hal.nose_fixed = false;
  r.hal.nose_at_mm = 120;
  r.run(10);
  r.send("10 DOCK 300 50");
  TEST_ASSERT_EQUAL_STRING("10 DONE", r.waitFor("10 ").c_str());
  TEST_ASSERT_FLOAT_WITHIN(1.0f, 120.0f, r.c.mm(AX_L));
  TEST_ASSERT_TRUE(r.has("EVT NOSE 1"));
}

void test_dock_gives_up() {
  Rig r;
  r.ready();
  r.hal.nose_fixed = false;
  r.hal.nose_at_mm = 500;
  r.run(10);
  r.send("10 DOCK 100 50");
  TEST_ASSERT_EQUAL_STRING("10 FAIL E_NODOCK", r.waitFor("10 ").c_str());
}

void test_stop_cancels_motion() {
  Rig r;
  r.ready();
  r.send("10 DRIVE 1000");
  r.run(200);
  ASSERT_REPLY("10 FAIL E_STOPPED", r.send("11 STOP"));
  TEST_ASSERT_TRUE(r.has("11 OK"));
  TEST_ASSERT_FALSE(r.c.busy());
}

// --- safety -------------------------------------------------------------------------------------

void test_estop_and_driver_reconfiguration() {
  Rig r;
  r.ready();
  r.send("10 Z 250");
  r.run(500);
  r.hal.vmot_v = 0;  // mushroom pressed: VMOT relay drops
  r.run(10);
  TEST_ASSERT_TRUE(r.has("10 FAIL E_ESTOP"));
  TEST_ASSERT_TRUE(r.has("EVT ESTOP"));
  TEST_ASSERT_FALSE(r.hal.en);
  TEST_ASSERT_FALSE(r.c.homed(AX_Z));
  ASSERT_REPLY("11 ERR E_ESTOP drivers not configured", r.send("11 ENABLE 1"));
  int calls = r.hal.configure_calls;
  r.hal.driver_ok = false;  // drivers not answering yet
  r.hal.vmot_v = 15;
  r.run(1000);
  TEST_ASSERT_TRUE(r.hal.configure_calls > calls);
  TEST_ASSERT_TRUE(r.c.estop());
  ASSERT_REPLY("12 ERR E_ESTOP drivers not configured", r.send("12 ENABLE 1"));
  r.hal.driver_ok = true;
  TEST_ASSERT_EQUAL_STRING("EVT ESTOP_CLEAR", r.waitFor("EVT ESTOP_CLEAR", 2000).c_str());
  ASSERT_REPLY("13 OK", r.send("13 ENABLE 1"));
  ASSERT_REPLY("14 ERR E_NOT_HOMED", r.send("14 Z 150"));
}

void test_driver_reset_detected() {
  Rig r;
  r.ready();
  r.hal.reset_flag = true;  // GSTAT.reset without a VMOT dip on the sense input
  std::string evt = r.waitFor("EVT DRIVER_RESET", 1000);
  TEST_ASSERT_EQUAL_STRING("EVT DRIVER_RESET", evt.c_str());
  TEST_ASSERT_FALSE(r.c.enabled());
  TEST_ASSERT_EQUAL_STRING("EVT ESTOP_CLEAR", r.waitFor("EVT ESTOP_CLEAR", 2000).c_str());
}

void test_limit_switch_outside_homing() {
  Rig r;
  r.ready();
  r.send("10 Z 150");
  r.waitFor("10 ");
  r.hal.ax[AX_Z].offset += static_cast<int32_t>(60 * 1600);  // lost steps: firmware thinks it is 60 mm higher
  r.send("11 Z 102");
  TEST_ASSERT_EQUAL_STRING("11 FAIL E_LIMIT", r.waitFor("11 ").c_str());
  TEST_ASSERT_TRUE(r.has("EVT LIMIT Z_HOME"));
  TEST_ASSERT_FALSE(r.c.homed(AX_Z));
}

// --- telemetry / config -------------------------------------------------------------------------

void test_status_telemetry() {
  Rig r;
  r.ready();
  r.hal.slot_a = true;
  r.hal.dock_v = 24;
  r.run(10);
  size_t mark = r.hal.out.size();
  char line[] = "20 STATUS";
  r.c.handleLine(line);
  TEST_ASSERT_EQUAL_STRING("20 OK", r.hal.out[mark].c_str());
  const std::string& tel = r.hal.out[mark + 1];
  float z, y, dock;
  int en;
  unsigned sw;
  char homed[4] = {};
  int n = sscanf(tel.c_str(), "TEL t=%*u z=%f y=%f l=%*f r=%*f en=%d busy= sw=%x vbat=%*f ibat=%*f vmot=%*f dock=%f "
                 "fa=P fb=P homed=%3s", &z, &y, &en, &sw, &dock, homed);
  TEST_ASSERT_EQUAL_INT_MESSAGE(6, n, tel.c_str());
  TEST_ASSERT_FLOAT_WITHIN(0.01f, 100.0f, z);
  TEST_ASSERT_EQUAL_INT(1, en);
  TEST_ASSERT_EQUAL_HEX(0x0F, sw);  // Z_HOME + Y_HOME (both at home), NOSE, SLOT_A
  TEST_ASSERT_EQUAL_STRING("ZY", homed);
  TEST_ASSERT_TRUE(r.has("EVT SLOT_A 1"));
}

void test_cfg() {
  Rig r;
  int calls = r.hal.configure_calls;
  ASSERT_REPLY("1 OK", r.send("1 CFG ycur 450"));
  TEST_ASSERT_EQUAL_UINT16(450, r.c.settings.run_ma[AX_Y]);
  TEST_ASSERT_EQUAL_INT(calls + 1, r.hal.configure_calls);
  ASSERT_REPLY("2 ERR E_ARG", r.send("2 CFG ycur 5000"));
  ASSERT_REPLY("3 ERR E_ARG", r.send("3 CFG warp 9"));
  ASSERT_REPLY("4 OK", r.send("4 CFG v_y 30"));
  TEST_ASSERT_EQUAL_FLOAT(30.0f, r.c.settings.v_y);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_parse_request);
  RUN_TEST(test_line_buffer_drops_overlong_lines);
  RUN_TEST(test_boot_and_ping);
  RUN_TEST(test_boot_without_vmot);
  RUN_TEST(test_homing_finds_switches);
  RUN_TEST(test_homing_with_broken_switch_wire_fails_safe);
  RUN_TEST(test_homing_without_switch_gives_up);
  RUN_TEST(test_axis_interlocks);
  RUN_TEST(test_y_needs_dock_unless_bench);
  RUN_TEST(test_z_move_and_speed_clamp);
  RUN_TEST(test_turn_direction_and_arc);
  RUN_TEST(test_vel_watchdog);
  RUN_TEST(test_dock_until_nose);
  RUN_TEST(test_dock_gives_up);
  RUN_TEST(test_stop_cancels_motion);
  RUN_TEST(test_estop_and_driver_reconfiguration);
  RUN_TEST(test_driver_reset_detected);
  RUN_TEST(test_limit_switch_outside_homing);
  RUN_TEST(test_status_telemetry);
  RUN_TEST(test_cfg);
  return UNITY_END();
}

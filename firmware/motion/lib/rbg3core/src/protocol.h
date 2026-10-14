// Pi <-> ESP32 line protocol (03-software §3): request tokenizer and number parsing.
#pragma once

#include <stddef.h>
#include <stdint.h>

namespace rbg3 {

constexpr size_t kMaxLine = 96;
constexpr int kMaxArgs = 4;

struct Request {
  uint16_t seq = 0;
  char cmd[12] = {};
  int argc = 0;
  const char* argv[kMaxArgs] = {};
};

// Splits `line` in place (spaces -> NUL). False if the line has no valid seq or command.
bool parseRequest(char* line, Request& out);

// Strict float parse of a whole token ("12", "-3.5"). False on garbage or empty.
bool parseNumber(const char* s, float& out);

// Accumulates bytes into lines. feed() returns true when `line()` holds a complete line.
class LineBuffer {
 public:
  bool feed(char c);
  char* line() { return buf_; }

 private:
  char buf_[kMaxLine + 1] = {};
  size_t len_ = 0;
  bool overflow_ = false;
};

}  // namespace rbg3

#include "protocol.h"

#include <stdlib.h>
#include <string.h>

namespace rbg3 {

static char* nextToken(char*& p) {
  while (*p == ' ' || *p == '\t') p++;
  if (!*p) return nullptr;
  char* start = p;
  while (*p && *p != ' ' && *p != '\t') p++;
  if (*p) *p++ = '\0';
  return start;
}

bool parseRequest(char* line, Request& out) {
  out = Request{};
  char* p = line;
  char* seq = nextToken(p);
  char* cmd = nextToken(p);
  if (!seq || !cmd) return false;
  char* end = nullptr;
  long n = strtol(seq, &end, 10);
  if (*end || n < 1 || n > 65535) return false;
  if (strlen(cmd) >= sizeof(out.cmd)) return false;
  out.seq = static_cast<uint16_t>(n);
  strcpy(out.cmd, cmd);
  char* arg;
  while ((arg = nextToken(p)) != nullptr) {
    if (out.argc == kMaxArgs) return false;
    out.argv[out.argc++] = arg;
  }
  return true;
}

bool parseNumber(const char* s, float& out) {
  if (!s || !*s) return false;
  char* end = nullptr;
  double v = strtod(s, &end);
  if (*end) return false;
  out = static_cast<float>(v);
  return true;
}

bool LineBuffer::feed(char c) {
  if (c == '\r') return false;
  if (c == '\n') {
    bool ok = !overflow_ && len_ > 0;
    buf_[len_] = '\0';
    len_ = 0;
    overflow_ = false;
    return ok;
  }
  if (len_ >= kMaxLine) {
    overflow_ = true;  // drop the whole line rather than execute a truncated command
    return false;
  }
  buf_[len_++] = c;
  return false;
}

}  // namespace rbg3

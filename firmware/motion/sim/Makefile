# Host simulator of the motion firmware (no PlatformIO needed): make -C sim
CXX ?= c++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra
CORE := ../lib/rbg3core/src
SRCS := main.cpp $(wildcard $(CORE)/*.cpp)

build/fwsim: $(SRCS) $(wildcard $(CORE)/*.h) fake_hal.h
	@mkdir -p build
	$(CXX) $(CXXFLAGS) -I$(CORE) -I. $(SRCS) -o $@

clean:
	rm -rf build
.PHONY: clean

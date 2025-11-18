TARGET=sclockadj

TARGETARCH := $(shell gcc -dumpmachine)

CFLAGS := -O2 -Wall -Wextra -Wformat -Wformat=2 -Wconversion -Wimplicit-fallthrough -Werror=format-security -Werror=implicit -Werror=int-conversion -Werror=incompatible-pointer-types -Wformat-overflow -Wformat-signedness -Wnull-dereference -Winit-self -Wmissing-include-dirs -Wshift-negative-value -Wshift-overflow -Wswitch-default -Wuninitialized -Walloca -Warray-bounds -Wfloat-equal -Wshadow -Wpointer-arith -Wundef -Wunused-macros -Wbad-function-cast -Wcast-qual -Wcast-align -Wwrite-strings -Wdate-time -Wstrict-prototypes -Wold-style-definition -Wredundant-decls -Winvalid-utf8 -Wvla -Wdisabled-optimization -Wstack-protector -Wdeclaration-after-statement -Wtrampolines -Wbidi-chars=any,ucn -Wformat-overflow=2 -Wformat-truncation=2 -Wshift-overflow=2 -Wtrivial-auto-var-init -Wstringop-overflow=3 -Wstrict-flex-arrays -Walloc-zero -Warray-bounds=2 -Wattribute-alias=2 -Wduplicated-branches -Wduplicated-cond -Wcast-align=strict -Wjump-misses-init -Wlogical-op -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=3 -fstack-clash-protection -fstack-protector-all -fno-delete-null-pointer-checks -fno-strict-aliasing -fstrict-flex-arrays=3 -ftrivial-auto-var-init=pattern -fPIE

LDFLAGS := -Wl,-z,nodlopen -Wl,-z,noexecstack -Wl,-z,relro -Wl,-z,now -Wl,--as-needed -Wl,--no-copy-dt-needed-entries -pie

ifeq (yes,$(patsubst x86_64%-linux-gnu,yes,$(TARGETARCH)))
CFLAGS += -fcf-protection=full
endif
ifeq (yes,$(patsubst aarch64%-linux-gnu,yes,$(TARGETARCH)))
CFLAGS += -mbranch-protection=standard
endif

all:
	gcc -g sclockadj.c -o $(TARGET) $(CFLAGS) $(LDFLAGS)

clean:
	rm -f -- $(TARGET)

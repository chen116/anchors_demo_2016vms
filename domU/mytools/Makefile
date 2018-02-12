# ##############################################################################
# User variables

# user variables can be specified in the environment or in the local make.conf file
-include make.conf

# Where is the LITMUS^RT userspace library source tree?
# By default, we assume that it resides in a sibling directory named 'liblitmus'.
#LIBLITMUS ?= ../liblitmus
LIBLITMUS ?= ../liblitmus

# Include default configuration from liblitmus.
# IMPORTANT: Liblitmus must have been built before this file exists.
include ${LIBLITMUS}/inc/config.makefile

# all sources
vpath %.c src/

# local include files
CPPFLAGS += -Iinclude/

# ##############################################################################
# Targets

all = myapp deadlineDetectFile testCtrlPage deadlineDetectFileOption

LDLIBS += -lrt -lm

.PHONY: all clean
all: ${all}
clean:
	rm -f ${all} *.o *.d

obj-mytool = mytool.o
obj-myapp = myapp.o

mytool: ${obj-mytool}
myapp: ${obj-myapp}


# dependency discovery
include ${LIBLITMUS}/inc/depend.makefile


#!/bin/sh

# This is just a quick script to test the benchmarks.  It runs
# the tracing tools and benchmarks, and parses the trace output
# at the end of execution.


ST_TRACE="/root/ft_tools/st-trace-schedule"

echo "Starting st_trace"
${ST_TRACE} -s mk &
ST_TRACE_PID="$!"
echo "st_trace pid: ${ST_TRACE_PID}"
sleep 1

if [ "$#" -ne 1 ]; then
	./myapp 1 200 1 &
	#./myapp 100 200 1 &
	#./myapp 3 10 1 &
	#./myapp 3 10 1 &
	#./myapp 3 10 1 &
else
	./myapp -c $1 1 200 1&
	#./myapp -c $1 100 200 1&
	#./myapp -c $1 3 10 1&
	#./myapp -c $1 3 10 1&
	#./myapp -c $1 3 10 1&
fi
sleep 2
release_ts

sleep 2

echo "Sending SIGUSR1 to st_trace"
kill -USR1 ${ST_TRACE_PID}
echo "Waiting for st_trace..."
wait ${ST_TRACE_PID}
sleep 1

/root/ft_tools/st-job-stats -m /dev/shm/*.bin


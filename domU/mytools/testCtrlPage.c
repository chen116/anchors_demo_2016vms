// File: deadlineDetectFile.c

// This benchmark is based on the base_task provided in the RT-Xen mailing 
// list and liblitmus.  We make use of the liblitmus libraries to pull the
// consumed and remaining budget. Consumed budget is equal to the execution 
// time.  

// The deadline is detected by checking the time at the end of the job
// execution and comparing to the deadline from the liblitmus syscall.






#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>

#include "litmus.h"

#define NS_PER_MS         1e6
#define NS_PER_US         1e3

#define LOOP_COUNT_1US 453l

// #define DEBUG

/* Catch errors.
 */
#define CALL( exp ) do { \
int ret; \
ret = exp; \
if (ret != 0) \
fprintf(stderr, "%s failed: %m\n", #exp);\
else \
fprintf(stderr, "%s ok.\n", #exp); \
} while (0)

/* Declare the periodically invoked job.
 * Returns 1 -> task should exit.
 *         0 -> task should continue.
 */
int job(void);

double wcet_f;
double period_f;
char filePath[60] = "/dev/shm/testDeadlines/";
char myPID[20];
FILE *fp;
int missedJobs = 0;

long long wcet_us;
long dur;
long count;

// These hold the values read from LITMUS-RT
lt_t currentBudget, remainingBudget;
// This is a pointer to the thread control page
struct control_page* pCtrlPage;



int main(int argc, char** argv)
{
    int do_exit, ret;
    struct rt_task param;

    sprintf(myPID,"%d",getpid());
    strcat(filePath,myPID);
    
    wcet_f = atof(argv[1]);    // in ms
    period_f = atof(argv[2]);  // in ms
    
    wcet_us = (int)(wcet_f*1000);	// Convert ms to us
    
    // wcet_frac = modf(wcet_f,&int_temp);
    // wcet_int = (int)(int_temp);
    
    dur = 1000 * atoi(argv[3]);     // in seconds -> to ms
    count = (dur / period_f);
    
    // printf("wcet_f: %f\tperiod_f: %f\twcet_us: %ld\tcount: %d\n",
    // wcet_f,period_f,wcet_us,count);
    
    /* Setup task parameters */
    memset(&param, 0, sizeof(param));
    // param.exec_cost = wcet_f * NS_PER_MS;
    // param.period = period_f * NS_PER_MS;
    param.exec_cost = wcet_f * NS_PER_MS;
    param.period = period_f * NS_PER_MS;
    // printf("param.exec: %ld\tparam.period: %ld\n",param.exec_cost, param.period);
    // return 0;
    param.relative_deadline = period_f * NS_PER_MS;
    
    /* What to do in the case of budget overruns? */
    param.budget_policy = NO_ENFORCEMENT;
    
    /* The task class parameter is ignored by most plugins. */
    param.cls = RT_CLASS_SOFT;
    param.cls = RT_CLASS_HARD;
    
    /* The priority parameter is only used by fixed-priority plugins. */
    param.priority = LITMUS_LOWEST_PRIORITY;
    
    /* The task is in background mode upon startup. */
    
    
    /*****
     * 1) Command line paramter parsing would be done here.
     */
    
    
    
    /*****
     * 2) Work environment (e.g., global data structures, file data, etc.) would
     *    be setup here.
     */
    
    
    
    /*****
     * 3) Setup real-time parameters.
     *    In this example, we create a sporadic task that does not specify a
     *    target partition (and thus is intended to run under global scheduling).
     *    If this were to execute under a partitioned scheduler, it would be assigned
     *    to the first partition (since partitioning is performed offline).
     */
    CALL( init_litmus() );
    
    /* To specify a partition, do
     *
     * param.cpu = CPU;
     * be_migrate_to(CPU);
     *
     * where CPU ranges from 0 to "Number of CPUs" - 1 before calling
     * set_rt_task_param().
     */
    CALL( set_rt_task_param(gettid(), &param) );
    
    
    /*****
     * 4) Transition to real-time mode.
     */
    CALL( task_mode(LITMUS_RT_TASK) );
    
    /* The task is now executing as a real-time task if the call didn't fail.
     */
    
    pCtrlPage = get_ctrl_page();

    ret = wait_for_ts_release();
    if (ret != 0)
        printf("ERROR: wait_for_ts_release()");
    
    
    /*****
     * 5) Invoke real-time jobs.
     */
    do {
        /* Wait until the next job is released. */
        sleep_next_period();
        /* Invoke job. */
        do_exit = job();
    } while (!do_exit);
    
    
    
    /*****
     * 6) Transition to background mode.
     */
    CALL( task_mode(BACKGROUND_TASK) );
    
    
    
    /*****
     * 7) Clean up, maybe print results and stats, and exit.
     */
    return 0;
}

int job(void)
{
    long long i = 0;
    long j = 0;
    // int bBudgetFlag;

    if(pCtrlPage!=NULL)
    {
        printf("IRQ: %lu\tdeadline: %llu\tirq_syscall:%lu\n",
            pCtrlPage->irq_count, pCtrlPage->deadline,pCtrlPage->ts_syscall_start);
    }

    
    /* Do real-time calculation. */
    for (i = 0; i < wcet_us; ++i) {
        for ( j = 0; j < LOOP_COUNT_1US; ++j )
            sqrt((double)j*(j+1));
    }
    
    --count;

    // Check for missed deadlines
    // currentBudget is how long the task has executed for
    // remainingBudget is how much of the allocated budget has been consumed
    get_current_budget(&currentBudget,&remainingBudget);

    if(remainingBudget==0)
    {
        // Right now, we just write back the fact that a deadline was missed 
        fp=fopen(filePath, "w+");
        missedJobs++;
        if(fp != NULL)
        {
            fprintf(fp,"%d", missedJobs);
            fclose(fp);
        }
        else
            printf("\t\tError with file\n");
    }
    
    if (count > 0) return 0;   // don't exit
    else return 1;             // exit
}

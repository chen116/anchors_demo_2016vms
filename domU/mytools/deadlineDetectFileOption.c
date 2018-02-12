// File: deadlineDetectFile.c

// This benchmark is based on the base_task provided in the RT-Xen mailing 
// list and liblitmus.  We make use of the liblitmus libraries to pull the
// consumed and remaining budget. Consumed budget is equal to the execution 
// time.  

// The deadline is detected by checking the time at the end of the job
// execution and comparing to the deadline from the liblitmus syscall.





#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <sys/time.h>
#include <time.h>

#include "litmus.h"

#define OPTSTR "dln:c:h"

#define NS_PER_MS         1e6
#define NS_PER_US         1e3

#define LOOP_COUNT_1US 225l

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
char myName[40];
FILE *fp;
int missedJobs = 0;
int calCount = LOOP_COUNT_1US;

long long wcet_us;
long dur;
long count;

// These hold the values read from LITMUS-RT
lt_t currentBudget, remainingBudget;
// This is a pointer to the thread control page
struct control_page* pCtrlPage;
struct timespec startTime;
struct timespec stopTime;


static void usage()
{
    fprintf(stderr,
        "Usage\n"
        "   deadlineDetectFileOptions [COMMON-OPTS] WCET PERIOD DURATION\n"
        "   WCET, PERIOD: given in ms\n"
        "   DURATION given in seconds\n"
        "\n"
        "Options:\n"
        "   -d: allow debug mode, for getting calibration counts (not-implemented)\n"
        "   -l: Ignore duration and run for infinite time\n"
        "   -n NAME: specify task name as NAME. Set to NoNameSet as default\n"
        "   -c CALCOUNT: specify amount of 1US computation as CALCOUNT\n"
        "   -h: Displays this message\n"
    );

}



int main(int argc, char** argv)
{
    int do_exit, ret, bInfiniteDur = false;
    struct rt_task param;
    int opt;

    strncpy(myName,"NoNameSet",40);

    while((opt=getopt(argc,argv,OPTSTR)) != -1)
    {
        switch(opt)
        {
            case 'd':
                break;
            case 'l':
                bInfiniteDur = true;
                break;
            case 'n':
                strncpy(myName,optarg,40);
                break;
            case 'c':
                calCount = atoi(optarg);
                break;
            case 'h':
                usage();
                exit(0);
                break;
            default:
                printf("Unrecognized %c, optarg %s, optopt: %c\n",
                    opt,
                    optarg,
                    optopt);
                break;
        }
    }


    // Setup path for writing output
    sprintf(myPID,"%d",getpid());
    strcat(filePath,myPID);
    
    // Calculate runtime parameters
    wcet_f = atof(argv[optind + 0]);    // in ms
    period_f = atof(argv[optind + 1]);  // in ms
    
    wcet_us = (int)(wcet_f*1000);	// Convert ms to us
        
    dur = 1000 * atoi(argv[optind + 2]);     // in seconds -> to ms
    count = (dur / period_f);

    printf("Name set: %s\n",myName);
    printf("WCET: %f\t, Period: %f\t, Duration: %ld\t, Count: %d\n",
        wcet_f,
        period_f,
        (bInfiniteDur) ? -1:dur,
        calCount);
            
    /* Setup task parameters */
    memset(&param, 0, sizeof(param));
    param.exec_cost = wcet_f * NS_PER_MS;
    param.period = period_f * NS_PER_MS;
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
    } while (!do_exit || bInfiniteDur);
    

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
    int err;
    lt_t endTime;
    // int bBudgetFlag;

    // Get the start time 
    err = clock_gettime(CLOCK_MONOTONIC, &startTime);
    if (err != 0)
        perror("clock_gettime");
    
    /* Do real-time calculation. */
    for (i = 0; i < wcet_us; ++i) {
        for ( j = 0; j < calCount; ++j )
            sqrt((double)j*(j+1));
    }
    
    --count;

    // Check for missed deadlines
    // currentBudget is how long the task has executed for
    // remainingBudget is how much of the allocated budget has been consumed
    get_current_budget(&currentBudget,&remainingBudget);

    // Get the end time
    err = clock_gettime(CLOCK_MONOTONIC, &stopTime);
    if (err != 0)
        perror("clock_gettime");
    endTime = (unsigned long long)(1E9 * stopTime.tv_sec + stopTime.tv_nsec);

    // printf("\tstart:%llu\tend:%llu\tduration:%llu\tdeadline: %llu\n",
    //     (unsigned long long)(1E9 * startTime.tv_sec + startTime.tv_nsec),
    //     endTime,
    //     currentBudget,
    //     pCtrlPage->deadline);

    // if(remainingBudget==0)
    if(endTime > pCtrlPage->deadline)
    {
        // Right now, we just write back the fact that a deadline was missed 
        fp=fopen(filePath, "w+");
        missedJobs++;
        if(fp != NULL)
        {
            // TotalJobsMissed Duration EndTime Deadline
            // Job parameters are most recent missed task
            fprintf(fp,"%s %d %llu %llu %llu", 
                myName,
                missedJobs, 
                endTime, 
                currentBudget, 
                pCtrlPage->deadline);
            fclose(fp);
        }
        else
            printf("\t\tError with file\n");
    }
    
    if (count > 0) return 0;   // don't exit
    else return 1;             // exit
}

"""Exercise production arithmetic: prevent cap bypass and unbounded boost."""
import pathlib, subprocess, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class PolicyTest(unittest.TestCase):
 def test_frame_boost_and_caps(self):
  header=ROOT/'kernel/include/linux/singularity_perf.h'
  self.assertTrue(header.exists(), 'frame-aware performance policy missing')
  code='''
#include <assert.h>
#include <limits.h>
#include "singularity_perf.h"
int main(void) {
 unsigned long ascending[]={200,400,600,800,1000};
 unsigned long descending[]={1000,800,600,400,200};
 assert(singularity_opp_floor(850,ascending,5)==800);
 assert(singularity_opp_floor(480,descending,5)==400);
 assert(singularity_opp_floor(200,descending,5)==200);
 assert(singularity_opp_floor(199,ascending,5)==0);
 assert(singularity_opp_floor(900,ascending,0)==0);
 assert(singularity_boost_duration(4, 3) == 120);
 assert(singularity_boost_duration(250, 3) == 250);
 assert(singularity_boost_duration(4, 2) == 4);
 assert(singularity_boost_duration(0, 3) == 0);
 assert(singularity_boost_duration(UINT_MAX, 3) == 1000);
 assert(singularity_gpu_target(200, 1000, 3, 1, 1) == 850);
 assert(singularity_gpu_target(200, 500, 3, 1, 1) == 425);
 assert(singularity_gpu_target(900, 500, 3, 1, 1) == 500);
 assert(singularity_gpu_target(200, 1000, 3, 0, 1) == 200);
 assert(singularity_gpu_target(200, 1000, 2, 1, 1) == 200);
 assert(singularity_gpu_target(200, 1000, 3, 1, 0) == 200);
 assert(singularity_gpu_target(1, 0, 3, 1, 1) == 0);
 assert(singularity_gpu_target(0, ULONG_MAX, 3, 1, 1) <= ULONG_MAX);
}
'''
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'test.c').write_text(code.replace('\"singularity_perf.h\"', '\"'+str(header)+'\"'))
   subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True)
 def test_boost_published_before_worker_runs(self):
  source=(ROOT/'kernel/drivers/cpufreq/cpu_boost.c').read_text()
  start=source.index('void cpu_boost_kick(')
  end=source.index('EXPORT_SYMBOL_GPL(cpu_boost_kick)',start)
  body=source[start:end]
  preamble=r"""
#include <assert.h>
#include <stdbool.h>
#include <limits.h>
#define NR_CPUS 8
#define spin_lock_irqsave(a,b) ((void)(a), (b)=0)
#define spin_unlock_irqrestore(a,b) ((void)(a), (void)(b))
#define READ_ONCE(a) (a)
unsigned long jiffies=10, boost_expires=0;
int pending_lock, boost_disable_work, pending_kick_enable[1], system_unbound_wq;
bool boost_suspended;
unsigned long msecs_to_jiffies(unsigned int n) { return n; }
unsigned long atomic_long_read(unsigned long *p) { return *p; }
int atomic_long_try_cmpxchg(unsigned long *p, unsigned long *old, unsigned long n) {
 if (*p != *old) { *old=*p; return 0; } *p=n; return 1;
}
int time_after(unsigned long a, unsigned long b) {return (long)(b-a)<0;}
void bitmap_fill(int *p,int n) { (void)n; *p=1; }
int kp_active_mode(void) {return 3;}
unsigned int singularity_boost_duration(unsigned int n,int mode) { (void)mode; return n; }
void mod_delayed_work(int q,int *w,unsigned long d) {
 (void)q;(void)w;(void)d;assert(pending_kick_enable[0]);
}
"""
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'test.c').write_text(preamble+body+'\nint main(void){cpu_boost_kick(4);}')
   subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True)
 def test_gpu_boost_uses_round_down_at_thermal_cap(self):
  src=(ROOT/'kernel/drivers/devfreq/devfreq.c').read_text()
  fn=src[src.index('int update_devfreq('):src.index('EXPORT_SYMBOL(update_devfreq)')]
  header=ROOT/'kernel/include/linux/singularity_perf.h'
  preamble=r"""
#include <assert.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#define DEVFREQ_NAME_LEN 16
#define DEVFREQ_FLAG_LEAST_UPPER_BOUND 1
#define lockdep_assert_held(p) ((void)(p))
typedef uint32_t u32;
struct devfreq;
struct governor { char name[16]; int (*get_target_freq)(struct devfreq *,unsigned long *); };
struct profile {unsigned long *freq_table;unsigned int max_state;};
struct devfreq {int lock;struct governor *governor;struct profile *profile;};
int kp_active_mode(void) {return 3;}
int cpu_boost_active(void) {return 1;}
void get_freq_range(struct devfreq *d,unsigned long *min,unsigned long *max) {
 (void)d; *min=100; *max=480;
}
int devfreq_set_target(struct devfreq *d,unsigned long f,u32 flags) {
 (void)d;assert(f==400); assert(flags & DEVFREQ_FLAG_LEAST_UPPER_BOUND);return 0;
}
int gov_target(struct devfreq *d,unsigned long *f) {(void)d;*f=200;return 0;}
"""
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'test.c').write_text('#include "'+str(header)+'"\n'+preamble+fn+'\nint main(void){struct governor g={"msm-adreno-tz",gov_target};unsigned long table[]={1000,800,600,400,200};struct profile profile={table,5};struct devfreq df={0,&g,&profile};return update_devfreq(&df);}')
   subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True)
 def test_boost_state_rejects_uninitialized_expiry_and_suspend(self):
  src=(ROOT/'kernel/drivers/cpufreq/cpu_boost.c').read_text()
  fn=src[src.index('bool cpu_boost_active('):src.index('static int boost_pm_event(')]
  preamble=r"""
#include <stdbool.h>
#include <assert.h>
#include <limits.h>
#define READ_ONCE(a) (a)
unsigned long jiffies,boost_expires;
bool boost_suspended;
unsigned long atomic_long_read(unsigned long *p){return *p;}
int time_before(unsigned long a,unsigned long b){return (long)(a-b)<0;}
"""
  main=r"""
int main(void) {
 jiffies=ULONG_MAX-100;boost_expires=0;assert(!cpu_boost_active());
 jiffies=10;boost_expires=12;assert(cpu_boost_active());
 jiffies=12;assert(!cpu_boost_active());
 jiffies=11;boost_suspended=true;assert(!cpu_boost_active());
}
"""
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'test.c').write_text(preamble+fn+main)
   subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True)
if __name__=='__main__':unittest.main()

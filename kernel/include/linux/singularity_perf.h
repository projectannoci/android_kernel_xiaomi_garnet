/* SPDX-License-Identifier: GPL-2.0 */
#ifndef _LINUX_SINGULARITY_PERF_H
#define _LINUX_SINGULARITY_PERF_H

/* Frame hints are short; hold the floor across adjacent render bursts. */
static inline unsigned int singularity_boost_duration(unsigned int ms, int mode)
{
	if (!ms)
		return 0;
	if (ms > 1000)
		ms = 1000;
	if (mode == 3 && ms < 120)
		ms = 120;
	return ms;
}

/* Caller supplies the current QoS/thermal ceiling, not the silicon maximum. */
static inline unsigned long singularity_gpu_target(unsigned long target,
		unsigned long ceiling, int mode, int active, int adreno)
{
	unsigned long floor;

	if (mode != 3 || !active || !adreno)
		return target;
	floor = (ceiling / 100) * 85 + ((ceiling % 100) * 85) / 100;
	if (target < floor)
		target = floor;
	if (target > ceiling)
		target = ceiling;
	return target;
}
/* KGSL's target callback requires an exact entry; it does not round Hz. */
static inline unsigned long singularity_opp_floor(unsigned long target,
		const unsigned long *table, unsigned int count)
{
	unsigned long best = 0;
	unsigned int i;

	for (i = 0; i < count; i++)
		if (table[i] <= target && table[i] > best)
			best = table[i];
	return best;
}
#endif

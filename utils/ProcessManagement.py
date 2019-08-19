import os
import psutil
import itertools
import logging
import random
from distributed import Worker
import sys
import time
from tornado.ioloop import IOLoop
from tornado import gen
from multiprocessing import Process

LOG_FORMAT = "%(levelname)-5s %(asctime)s %(filename)-20s %(funcName)-25s %(lineno)-5d: %(message)s"


def generate_worker_names(total=None):
	iterator = itertools.count() if total is None else range(total)
	for idx in iterator:
		yield "worker-{}".format(idx)


def spawn_worker(name, scheduler, memory_limit, local_dir="./tmp/", ncores=1, logfile=None, memory_pause_fraction=0.95, **kwargs):
	memory_pause_fraction = float(memory_pause_fraction)
	proc = psutil.Process(os.getpid())

	if logfile is not None:
		log = open(logfile, 'a')
		sys.stdout = log
		sys.stderr = log

	os.environ['MKL_NUM_THREADS'] = '1'

	loop = IOLoop.current()

	n = Worker('tcp://{}'.format(scheduler), silence_logs=logging.WARN, 
											 ncores=ncores, 
											 memory_limit=memory_limit, 
											 name=name, 
											 local_dir=local_dir, 
											 memory_spill_fraction=1.0,
											 memory_target_fraction=1.0,
											 memory_pause_fraction=1.0,
											 **kwargs)

	memory_limit = n.memory_limit

	@gen.coroutine
	def monitor_worker():
		yield n.start()
		while n.status != 'closed':
			memory = proc.memory_info().rss
			frac = memory / memory_limit if memory_limit > 0 else 0
			if frac > memory_pause_fraction:
				print('Worker Exceeded Memory Limit: {}/{}'.format(frac, memory_pause_fraction))
				n.stop()
				yield n._close(report=False, nanny=False, executor_wait=True, timeout=2)
				raise gen.Return()
			yield gen.sleep(2)

	try:
		loop.run_sync(monitor_worker)
	except (KeyboardInterrupt, TimeoutError):
		pass
	finally:
		print('Killing Worker {}'.format(name))

	return True

	
def start(n_workers=8, localhost='127.0.0.1:8786', memory_limit='4GB'):
	worker_names = (name for name in generate_worker_names())
	proc_gen = (Process(target=spawn_worker, args=(name, localhost, memory_limit)) for name in worker_names)
	procs = [next(proc_gen) for idx in range(n_workers)]
	for proc in procs:
		proc.daemon = True
	[proc.start() for proc in procs]
	time.sleep(10)
	return procs


def stop(procs):
	for proc in procs:
		proc.terminate()	
# Code from Stack Overflow question:
# https://stackoverflow.com/questions/57354700/starmap-combined-with-tqdm
# Question authored by sdgaw erzswer:
# https://stackoverflow.com/users/3523464/sdgaw-erzswer
# Answer authored by Darkonaut:
# https://stackoverflow.com/users/9059420/darkonaut

# istarmap.py for Python 3.8+
import multiprocessing.pool as mpp


def istarmap(self, func, iterable, chunksize=1):
    """starmap-version of imap
    """
    self._check_running()
    if chunksize < 1:
        raise ValueError(
            "Chunksize must be 1+, not {0:n}".format(
                chunksize))

    task_batches = mpp.Pool._get_tasks(func, iterable, chunksize)
    result = mpp.IMapIterator(self)
    self._taskqueue.put(
        (
            self._guarded_task_generation(result._job,
                                          mpp.starmapstar,
                                          task_batches),
            result._set_length
        ))
    return (item for chunk in result for item in chunk)

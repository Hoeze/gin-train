"""
Module implementing different samplers
"""
import pandas as pd
import numpy as np
from kipoi_utils.external.torch.sampler import Sampler
from kipoi.data_utils import iterable_cycle
import warnings
import gin


def get_batch_sizes(p_vec, batch_size, verbose=True):
    """Compute the individual batch sizes for different probabilities

    Args:
      p_vec: list of probabilities for each class
      batch_size: batch size

    Returns:
      rounded list p_vec[i]*batch_size
    """
    p_vec = np.array(p_vec) / sum(p_vec)

    batch_sizes = np.round(p_vec * batch_size).astype(int)
    difference = batch_size - batch_sizes.sum()
    # Increase the largest one
    batch_sizes[batch_sizes.argmax()] += difference
    if verbose:
        print("Using batch sizes:")
        print(batch_sizes)
    assert batch_sizes.sum() == batch_size
    return batch_sizes


class StratifiedRandomBatchSampler(Sampler):

    def __init__(self, class_vector, p_vec, batch_size, verbose=False):
        """Stratified Sampling

        Args:
          class_vector (np.array): a vector of class labels
          p_vec (list[float]): list of probabilities for each class
          batch_size (int): batch_size
          verbose
        """
        self.n_splits = int(class_vector.shape[0] / batch_size)
        self.class_vector = class_vector
        self.p_vec = p_vec
        self.batch_size = batch_size

        self.batch_sizes = get_batch_sizes(self.p_vec, self.batch_size, verbose=verbose)

        # check that the individual batch size will always be > 0
        for i, batch_size in enumerate(self.batch_sizes):
            if batch_size == 0:
                warnings.warn("Batch size for class {} is 0.".format(i))

        self.classes = np.arange(len(p_vec))
        assert np.all(np.sort(pd.Series(self.class_vector).unique()) == self.classes)

        idx_all = np.arange(len(self.class_vector))
        self.class_idx_iterators = [iterable_cycle(np.random.permutation(idx_all[self.class_vector == cls]))
                                    for cls in self.classes]

    def __iter__(self):
        for i in range(len(self)):
            yield [next(self.class_idx_iterators[i])
                   for i, batch_size in enumerate(self.batch_sizes)
                   for j in range(batch_size)]

    def __len__(self):
        return len(self.class_vector) // self.batch_size

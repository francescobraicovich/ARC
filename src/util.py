#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import torch
import numpy as np
import logging


def to_numpy(var, device=None):
    """
    Convert a PyTorch tensor to a NumPy array, handling the device.

    Args:
        var (torch.Tensor): The PyTorch tensor to convert.
        device (torch.device or None): The device type (e.g., 'cuda', 'mps', 'cpu').

    Returns:
        np.ndarray: The NumPy array.
    """
    if not isinstance(var, torch.Tensor):
        raise TypeError("Input must be a PyTorch tensor.")

    # Move tensor to the specified device if provided
    if device is not None:
        var = var.to(device)

    # Ensure the tensor is on CPU before converting to NumPy
    if var.device.type != 'cpu':
        var = var.cpu()

    # Detach from the computational graph and convert to NumPy
    return var.detach().numpy()

def to_tensor(ndarray, requires_grad=False, device=None):
    """
    Convert a NumPy array to a PyTorch tensor with the specified gradient and device settings.
    """
    tensor = torch.from_numpy(ndarray).float()
    if device:
        tensor = tensor.to(device)
    tensor.requires_grad = requires_grad
    return tensor

def soft_update(target, source, tau_update):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(
            target_param.data * (1.0 - tau_update) + param.data * tau_update
        )

def hard_update(source_network, target_network):
    for target_param, source_param in zip(target_network.parameters(), source_network.parameters()):
        np_data = source_param.detach().cpu().numpy()  # Convert to NumPy
        # NOTE:
        # Converting the source tensor to a NumPy array before copying works because:
        # 1. It ensures that the data is copied to a completely independent memory buffer,
        #    avoiding any shared memory issues that might arise in PyTorch.
        # 2. The NumPy conversion forces synchronization of operations, especially on GPUs,
        #    resolving potential conflicts from PyTorch's asynchronous execution model.
        # 3. It bypasses PyTorch's autograd mechanism and tensor metadata handling, which 
        #    could cause segmentation faults if there are hidden issues with gradient tracking 
        #    or tensor metadata inconsistencies.
        # While effective, this approach involves additional overhead due to data transfer and 
        # should only be used when other methods (e.g., .clone(), .detach()) fail to work.
        target_param.data = torch.from_numpy(np_data).to(target_param.device)  # Convert back


def get_output_folder(parent_dir, env_name):
    """Return save folder.

    Assumes folders in the parent_dir have suffix -run{run
    number}. Finds the highest run number and sets the output folder
    to that number + 1. This is just convenient so that if you run the
    same script multiple times tensorboard can plot all of the results
    on the same plots with different names.

    Parameters
    ----------
    parent_dir: str
      Path of the directory containing all experiment runs.

    Returns
    -------
    parent_dir/run_dir
      Path to this run's save directory.
    """
    os.makedirs(parent_dir, exist_ok=True)
    experiment_id = 0
    for folder_name in os.listdir(parent_dir):
        if not os.path.isdir(os.path.join(parent_dir, folder_name)):
            continue
        try:
            folder_name = int(folder_name.split('-run')[-1])
            if folder_name > experiment_id:
                experiment_id = folder_name
        except:
            pass
    experiment_id += 1

    parent_dir = os.path.join(parent_dir, env_name)
    parent_dir = parent_dir + '-run{}'.format(experiment_id)
    os.makedirs(parent_dir, exist_ok=True)
    return parent_dir


def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)
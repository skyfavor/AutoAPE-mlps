# -*- coding: utf-8 -*-
# Author : Jin Kim
# e-mail : jinkim@seculayer.co.kr
# Powered by Seculayer © 2021 Service Model Team, R&D Center.
import os
import json
import tensorflow as tf
from typing import List

from mlps.core.apeflow.interface.distribute.tf.TFDistributeRunnerV2 import TFDistributeRunnerV2
from mlps.core.apeflow.interface.model.ModelAbstract import ModelAbstract
from mlps.core.apeflow.api.algorithms.AlgorithmAbstract import AlgorithmAbstract
from mlps.core.apeflow.api.algorithms.AlgorithmFactory import AlgorithmFactory


def strategy_decorator(func):
    def wrapper(*args, **kwargs):
        dist_runner: TFDistributeRunnerV2 = TFDistributeRunnerV2()
        with dist_runner.get_strategy().scope():
            func(*args, **kwargs)
    return wrapper()


class TFModel(ModelAbstract):
    def __init__(self, param_dict: dict, ext_data=None):
        ModelAbstract.__init__(self, param_dict, ext_data)
        self.distribute_runner = TFDistributeRunnerV2()
        self.model = self._build()

    @strategy_decorator
    def _build(self) -> AlgorithmAbstract:
        model = AlgorithmFactory.create(param_dict=self.param_dict, ext_data=self.ext_data)
        model.load_model()

        return model

    @strategy_decorator
    def learn(self, dataset):
        # learning
        self.model.learn(dataset)
        self.model.saved_model()

    @strategy_decorator
    def eval(self, dataset):
        # learning
        result = self.model.eval(dataset)
        return result

    @strategy_decorator
    def predict(self, x):
        result: List = self.model.predict(x)
        return result


if __name__ == '__main__':
    from mlps.common.Constants import Constants
    from mlps.common.Common import Common
    Common.TF_BACKEND_VER = Constants.TF_BACKEND_V2
    tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)

    _param_dict = {
        "algorithm_code": "KDNN",
        "algorithm_type": "Classifier",
        "data_type": "Single",
        "method_type": "Basic",
        "input_units": "5",
        "output_units": "2",
        "hidden_units": "5,4,3",
        "global_step": "10",
        "dropout_prob": "0.5",
        "optimizer_fn": "Adam",
        "model_nm": "KDNN",
        "alg_sn": "0",
        "job_type": "learn",
        "depth": "0",
        "global_sn": "0",
        "learning_rate": "0.1",
        "initial_weight": "0.1",
        "num_layer": "5",
        "act_fn": "ReLU"
    }

    cluster = {
        "worker": ["192.168.2.235:9305"],
        # "worker": ["192.168.2.235:9305", "192.168.2.235:9306"],
    }
    task_idx = 0
    os.environ["TF_CONFIG"] = json.dumps({
        "cluster": cluster,
        "task": {"type": "worker", "index": int(task_idx)}
    })
    os.environ["CUDA_VISIBLE_DEVICES"] = str(task_idx)

    _model = TFModel(_param_dict)
    # model.build()

    import numpy as np
    num_samples = 1000
    input_units = int(_param_dict["input_units"])
    _x = np.random.random((num_samples, input_units))
    tmp = np.array([[1] for i in range(num_samples)])
    sum_x = np.sum(_x, axis=1).reshape((-1, 1))
    y = np.where(sum_x > 2.0, tmp, 0 * tmp)
    y = np.concatenate((y, 1 - y), axis=1)
    _x = tf.cast(_x, tf.float32)
    data = {"x" : _x, "y" : y}
    _model.learn(data)

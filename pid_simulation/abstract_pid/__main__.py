from pid import PID
from multi_pid import (PidConfig, MultiPid, AggregatingPid)
from linear_functions import (
    SimpleLinear, NoisedLinear, MultiFunSimoCO,
    simple_linear
)
from target_providers import TargetProviderFromFunction
from logger import (Logger, MultiPidLogger, AggregatingLogger)
from simulator import Simulator

import json


def test_multi_pid():
    f1 = simple_linear(k=2, b=2)
    target1 = TargetProviderFromFunction(lambda t: 20 if t < 50 else 40)
    f2 = simple_linear(k=1, b=1)
    target2 = TargetProviderFromFunction(lambda t: 40 if t < 50 else 5)

    pid1_config = PidConfig(target1, k_p=0.1, k_i=0.4, k_d=-0.1)
    pid2_config = PidConfig(target2, k_p=0.1, k_i=0.4, k_d=-0.1)

    simo_object = MultiFunSimoCO({
        'cpu': f1,
        'ram': f2
    })

    pid = MultiPid(simo_object, {'cpu': pid1_config, 'ram': pid2_config}, period=1)

    output_lines = []
    logger = MultiPidLogger(pid=pid, output_lines=output_lines, period=1)

    simulator = Simulator([pid, logger])
    # simulator = Simulator([pid])
    simulator.simulate(200)

    # ====--------plotting--------------
    with open('multipid_test.json', 'w') as out:
        for ddict in output_lines:
            jout = json.dumps(ddict) + '\n'
            out.write(jout)


def test_aggregating_pid():
    f1 = simple_linear(k=2, b=2)
    target1 = TargetProviderFromFunction(lambda t: 20 if t < 50 else 40)
    f2 = simple_linear(k=1, b=1)
    target2 = TargetProviderFromFunction(lambda t: 40 if t < 50 else 5)

    simo_object = MultiFunSimoCO({
        'cpu': f1,
        'ram': f2
    })

    pid = AggregatingPid(
        simo_object,
        target_providers={
            'cpu': target1,
            'ram': target2
        },
        k_p=-2,
        k_i=-4,
        k_d=0, period=1
    )

    output_lines = []
    logger = AggregatingLogger(pid=pid, output_lines=output_lines, period=0.5)

    simulator = Simulator([pid, logger])
    simulator.simulate(200)

    # ====--------plotting--------------
    with open('aggregating_test.json', 'w') as out:
        for ddict in output_lines:
            jout = json.dumps(ddict) + '\n'
            out.write(jout)


if __name__ == "__main__":
    # # controlled_object = SimpleLinear(k=2, b=2)
    # controlled_object = NoisedLinear(k=2, b=2, deviation=0.5)
    #
    # def step(t: float) -> float:
    #     if 35 < t < 65:
    #         return 10
    #     else:
    #         return 0
    #
    # target_provider = TargetProviderFromFunction(step)
    # driver = IdentityDriver()
    #
    # pid = PID(
    #     k_p=0.4,
    #     k_i=0.5,
    #     k_d=-0.2,
    #     controlled_object=controlled_object,
    #     target_provider=target_provider,
    #     driver=driver,
    #     period=1
    # )
    # output_lines = []
    # logger = Logger(controlled_object=controlled_object, target_provider=target_provider, pid=pid,
    #                 output_lines=output_lines, period=1)
    #
    # simulator = Simulator([pid, logger])
    # simulator.simulate(100)
    #
    # # ====--------plotting--------------
    # with open('json_data.json', 'w') as out:
    #     for ddict in output_lines:
    #         jout = json.dumps(ddict) + '\n'
    #         out.write(jout)

    # test_multi_pid()
    test_aggregating_pid()

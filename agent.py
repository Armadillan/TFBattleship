#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pickle

import tensorflow as tf

from tf_agents.environments import tf_py_environment
from tf_agents.environments import wrappers
from tf_agents.agents.dqn import dqn_agent
from tf_agents.drivers import dynamic_step_driver, dynamic_episode_driver
from tf_agents.metrics import tf_metrics
from tf_agents.networks import q_network
from tf_agents.policies import random_tf_policy
from tf_agents.policies.policy_saver import PolicySaver
from tf_agents.replay_buffers import tf_uniform_replay_buffer
from tf_agents.utils import common

from env import PyBattleshipEnv

NAME = "TEST9"

FC_LAYER_PARAMS = (100, 50)

LEARNING_RATE = 1e-9 # Learning rate for optimizer

ACTIVATION_FN = tf.keras.activations.relu

OPTIMIZER = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
LOSS_FN = common.element_wise_squared_loss

BUFFER_MAX_LEN = 100
BUFFER_BATCH_SIZE = 10

COLLECTION_STEPS = 1
NUM_EVAL_EPISODES = 10
NUM_TRAINING_ITERATIONS = 20_000

# Initial epsilon (chance for collection policy to pick random move)
INITIAL_EPSILON = 0.99
END_EPSILON = 0.1 # End epsilon
EPSILON_DECAY_STEPS = 18_000 # How many steps the epsilon should decay over

SKIP_INVALID_ACTIONS = False
PUNISH_INVALID_ACTIONS = True # Takes precedence over SKIP_INVALID_ACTIONS

LOG_INTERVAL = 5 # How often to print progress to console
EVAL_INTERVAL = 10 # How often to evaluate the agent's performence

# Where to save checkpoints, policies and stats
SAVE_DIR = os.path.join("..", "TFBattleship_DATA")

train_py_env = PyBattleshipEnv(skip_invalid_actions=SKIP_INVALID_ACTIONS)
eval_py_env = PyBattleshipEnv(skip_invalid_actions=SKIP_INVALID_ACTIONS)

train_py_env = wrappers.TimeLimit(train_py_env, duration=100)
eval_py_env = wrappers.TimeLimit(eval_py_env, duration=100)

train_env = tf_py_environment.TFPyEnvironment(train_py_env)
eval_env = tf_py_environment.TFPyEnvironment(eval_py_env)

# Creates a tensor to count the number of training iterations
train_step_counter = tf.Variable(0)

q_net = q_network.QNetwork(
        train_env.observation_spec(), # Passes observation spec,
        train_env.action_spec(), # and action spec of environment.
        fc_layer_params=FC_LAYER_PARAMS,
        activation_fn=ACTIVATION_FN
)

epsilon = tf.compat.v1.train.polynomial_decay(
    learning_rate=INITIAL_EPSILON,
    global_step=train_step_counter,
    decay_steps=EPSILON_DECAY_STEPS,
    end_learning_rate=END_EPSILON
)

agent = dqn_agent.DqnAgent(
    time_step_spec=train_env.time_step_spec(),
    action_spec=train_env.action_spec(),
    q_network=q_net,
    optimizer=OPTIMIZER,
    epsilon_greedy=epsilon,
    td_errors_loss_fn=LOSS_FN,
    train_step_counter=train_step_counter
)

replay_buffer = tf_uniform_replay_buffer.TFUniformReplayBuffer(
    data_spec=agent.collect_data_spec,
    batch_size=train_env.batch_size,
    max_length=BUFFER_MAX_LEN,
)

replay_observer = [replay_buffer.add_batch]

dataset = replay_buffer.as_dataset(
    sample_batch_size=BUFFER_BATCH_SIZE,
    num_steps = 2,
    num_parallel_calls=3
).prefetch(3)

dataset_iterator = iter(dataset)

agent.initialize()

agent.train = common.function(agent.train)

agent.train_step_counter.assign(0)

collect_driver = dynamic_step_driver.DynamicStepDriver(
    env=train_env,
    policy=agent.collect_policy,
    observers=replay_observer, # Passes the replay buffer observer
    num_steps=COLLECTION_STEPS
)

random_policy_driver = dynamic_step_driver.DynamicStepDriver(
    env=train_env,
    policy=random_tf_policy.RandomTFPolicy(
        train_env.time_step_spec(), train_env.action_spec()
        ),
    observers=replay_observer,
    num_steps=COLLECTION_STEPS
)

avg_episode_len_metric = tf_metrics.AverageEpisodeLengthMetric()
avg_return_metric = tf_metrics.AverageReturnMetric()

eval_metrics = [
    avg_episode_len_metric,
    avg_return_metric
]

policy_saver = PolicySaver(agent.policy)

eval_driver = dynamic_episode_driver.DynamicEpisodeDriver(
    env=eval_env,
    policy=agent.policy,
    observers=eval_metrics,
    num_episodes=NUM_EVAL_EPISODES
)

train_env.reset()
eval_env.reset()

final_time_step, _ = collect_driver.run()

# Initial buffer fill using random policy
for i in range(max(int(BUFFER_MAX_LEN/COLLECTION_STEPS), 1)):
    # Can alternatively be run with the collection policy like so:
    # final_time_step, _ = collect_driver.run(final_time_step)
    final_time_step, _ = random_policy_driver.run(final_time_step)

eval_driver.run()

avg_episode_len = avg_episode_len_metric.result().numpy()
avg_return = avg_return_metric.result().numpy()

episode_lengths = [avg_episode_len]
returns = [avg_return]
losses = []

for metric in eval_metrics:
    metric.reset()

checkpointer = common.Checkpointer(
    ckpt_dir=os.path.join(SAVE_DIR, NAME + " data", "checkpoints"),
    max_to_keep=20,
    agent=agent,
    policy=agent.policy,
    replay_buffer=replay_buffer,
    global_step=agent.train_step_counter,
    network=q_net
)


# MAIN TRAINING LOOP
for _ in range(NUM_TRAINING_ITERATIONS):

    # Runs collect driver
    final_time_step, _ = collect_driver.run(final_time_step)

    # Gets experiance from buffer
    experience, _ = next(dataset_iterator)

    # Train the agent and get the loss
    train_loss = agent.train(experience).loss

    # Save the loss to the losses list
    losses.append(train_loss.numpy())

    # Gets the number of training steps completed
    step = agent.train_step_counter.numpy()

    # Prints progress to console
    if step % LOG_INTERVAL == 0:
        print('step = {0}: loss = {1}'.format(step, train_loss))

    # Evaluates agent performence
    if step % EVAL_INTERVAL == 0:

        # Runs evaluation driver
        eval_driver.run()

        avg_episode_len = avg_episode_len_metric.result().numpy()
        avg_return = avg_return_metric.result().numpy()

        print(f'Average episode length: {avg_episode_len}')

        episode_lengths.append(avg_episode_len)
        returns.append(avg_return)

        # Saves agent policy
        policy_saver.save(
            os.path.join(
                SAVE_DIR, NAME + " data", "policy saves",
                NAME + " policy @ " + str(step)
            )
        )

        # Runs checkpointer to make a backup of the agent, network etc.
        checkpointer.save(step)

        # Saves the lists of statistics as a pickled dictionary
        with open(
                os.path.join(SAVE_DIR, NAME + " data", NAME + " stats.pkl"),
                "wb",
                ) as file:
            pickle.dump(
                {"Lengths": episode_lengths,
                 "Losses": losses},
                file
                )

        # Resets all metrics
        for metric in eval_metrics:
            metric.reset()

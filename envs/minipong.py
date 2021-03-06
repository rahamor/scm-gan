import time
import numpy as np
import random

from tqdm import tqdm
from multi_env import MultiEnvironment
from gym.spaces.discrete import Discrete

GAME_SIZE = 64
dataset = None

def init():
    global dataset
    dataset = build_dataset()


class MinipongEnv():
    def __init__(self):
        self.reset()
        self.action_space = Discrete(4)

    def reset(self):
        self.left_y = np.random.randint(0, 64)
        self.right_y = np.random.randint(0, 64)
        self.ball_x = np.random.randint(0, 64)
        self.ball_y = np.random.randint(0, 64)
        self.state = build_state(self.left_y, self.right_y, self.ball_x, self.ball_y)

    # The agent can press one of four buttons
    def step(self, a):
        # Some dimensions change in reaction to the agent's actions
        if a == 0:
            self.right_y -= 3
        elif a == 1:
            self.right_y += 3
        self.right_y %= 64

        if a == 2:
            self.left_y -= 3
        elif a == 3:
            self.left_y += 3
        self.left_y %= 64

        # Other dimensions change, but not based on agent actions
        self.ball_x += 3
        self.ball_x %= 64
        self.state = build_state(self.left_y, self.right_y, self.ball_x, self.ball_y)
        return self.state, 0, False, {}


def build_state(left_y, right_y, ball_x, ball_y):
    state = np.zeros((3, GAME_SIZE, GAME_SIZE))
    paddle_width = 1
    paddle_height = 4
    ball_size = 2
    left_x = 4
    right_x = GAME_SIZE - 4

    left_y = np.clip(left_y, paddle_height, GAME_SIZE - paddle_height)
    right_y = np.clip(right_y, paddle_height, GAME_SIZE - paddle_height)
    ball_x = np.clip(ball_x, paddle_height, GAME_SIZE - paddle_height)
    ball_y = np.clip(ball_y, paddle_height, GAME_SIZE - paddle_height)

    state[:, left_y - paddle_height:left_y + paddle_height,
               left_x - paddle_width: left_x + paddle_width] = 1.0
    state[:, right_y - paddle_height:right_y + paddle_height,
               right_x - paddle_width: right_x + paddle_width] = 1.0
    state[:, ball_y-ball_size:ball_y+ball_size,
               ball_x-ball_size:ball_x+ball_size] = 1.0
    return state


def build_dataset(num_actions=4, size=50000):
    dataset = []
    for i in tqdm(range(size)):
        env = MinipongEnv()
        before = np.array(env.state)
        action = np.random.randint(num_actions)
        env.step(action)
        after = np.array(env.state)
        dataset.append((before, action, after))
    return dataset  # list of tuples


def get_batch(size=32):
    idx = np.random.randint(len(dataset) - size)
    inputs, actions, targets = zip(*dataset[idx:idx + size])
    return inputs, actions, targets


# Continuous inputs are in the range [0, 1] for each dimension
def generate_image_continuous(factors):
    left_y = int(factors[0] * GAME_SIZE) + 0
    right_y = int(factors[1] * GAME_SIZE) + 0
    ball_x = int(factors[2] * GAME_SIZE) + 0
    ball_y = int(factors[3] * GAME_SIZE) + 0
    return build_state(left_y, right_y, ball_x, ball_y)


def simulator(factor_batch):
    batch_size = len(factor_batch)
    images = []
    for i in range(batch_size):
        images.append(generate_image_continuous(factor_batch[i]))
    return np.array(images)


def get_trajectories(batch_size=32, timesteps=10, policy=None):
    envs = MultiEnvironment([MinipongEnv() for _ in range(batch_size)])
    t_states, t_rewards, t_dones, t_actions = [], [], [], []
    for t in range(timesteps):
        actions = np.random.randint(envs.action_space.n, size=(batch_size,))
        states, rewards, dones, _ = envs.step(actions)
        t_states.append(states)
        t_rewards.append(rewards)
        t_dones.append(dones)
        t_actions.append(actions)
    # Reshape to (batch_size, timesteps, ...)
    states = np.swapaxes(t_states, 0, 1)
    rewards = np.swapaxes(t_rewards, 0, 1)
    dones = np.swapaxes(t_dones, 0, 1)
    actions = np.swapaxes(t_actions, 0, 1)
    return states, rewards, dones, actions

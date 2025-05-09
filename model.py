# -*- coding: utf-8 -*-
"""model

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1c4_i3N8vuf-TEU8votdi_QJt8dxCHV_a
"""

import torch
import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.envs import DummyVecEnv
from stable_baselines3.common.vec_env import VecNormalize
import gym
import os

# Định nghĩa lớp LSTM cho PPO
class LSTMPPOPolicy(ActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tạo lớp LSTM với kích thước đầu vào và đầu ra
        self.lstm = nn.LSTM(input_size=self.observation_space.shape[0], hidden_size=256, batch_first=True)

        # Định nghĩa lớp actor và critic
        self.actor = nn.Linear(256, self.action_space.n)
        self.critic = nn.Linear(256, 1)

    def forward(self, obs, *args, **kwargs):
        """
        Hàm xử lý đầu vào (state) qua LSTM.
        obs: đầu vào trạng thái, có thể là mảng 2D hoặc 3D (batch_size, seq_len, feature_dim)
        """
        # Thêm một chiều mới cho seq_len (nếu cần)
        if len(obs.shape) == 2:  # Nếu chỉ có batch_size, feature_dim
            obs = obs.unsqueeze(1)  # Thêm chiều sequence (seq_len=1)

        x, _ = self.lstm(obs)  # LSTM trả về cả output và hidden states
        x = x[:, -1, :]  # Lấy output của bước cuối cùng trong chuỗi thời gian
        action = self.actor(x)
        value = self.critic(x)
        return action, value

# Hàm huấn luyện PPO với chính sách LSTM
def train_ppo_lstm(env, total_timesteps=10_000, checkpoint_freq=10_000, checkpoint_dir="./checkpoints", tensorboard_log="./tensorboard_logs", **ppo_kwargs):
    os.makedirs(checkpoint_dir, exist_ok=True)
    os.makedirs(tensorboard_log, exist_ok=True)

    # Kiểm tra môi trường có phải là VecEnv hay không
    if not hasattr(env, "num_envs"):
        env = DummyVecEnv([lambda: env])
        env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)
    else:
        env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.0)

    # Tạo mô hình PPO với chính sách LSTM
    model = PPO(
        LSTMPPOPolicy,
        env,
        verbose=1,
        tensorboard_log=tensorboard_log,
        **ppo_kwargs
    )

    # Huấn luyện mô hình
    model.learn(total_timesteps=total_timesteps)

    # Lưu mô hình sau khi huấn luyện
    model.save("ppo_lstm_trading_model")

    return model

# Tạo môi trường giao dịch (ví dụ VN30TradingEnv hoặc bất kỳ môi trường nào bạn đã định nghĩa)
# Bạn có thể thay thế môi trường dưới đây với môi trường thực tế của bạn.
env = gym.make('CartPole-v1')  # Ví dụ môi trường CartPole

# Huấn luyện mô hình PPO-LSTM
trained_model = train_ppo_lstm(
    env,
    total_timesteps=10000,
    checkpoint_freq=1000,
    checkpoint_dir="./checkpoints",
    tensorboard_log="./tensorboard_logs"
)
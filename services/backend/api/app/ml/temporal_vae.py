"""PyTorch implementation of the showcase Aegis temporal attention VAE.

The live hybrid engine remains operational when a checkpoint is unavailable. This
module is imported only by training/inference adapters so FastAPI can still expose
deterministic demo scoring while model artifacts are being prepared.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch import Tensor, nn
import torch.nn.functional as F


SEQUENCE_LENGTH = 20
HIDDEN_SIZE = 64
LATENT_SIZE = 16


@dataclass(slots=True)
class TemporalVAEOutput:
    reconstruction: Tensor
    mean: Tensor
    log_variance: Tensor
    attention_weights: Tensor


class TemporalAttention(nn.Module):
    def __init__(self, hidden_size: int = HIDDEN_SIZE) -> None:
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1, bias=False),
        )

    def forward(self, encoded: Tensor) -> tuple[Tensor, Tensor]:
        logits = self.projection(encoded).squeeze(-1)
        weights = torch.softmax(logits, dim=1)
        context = torch.sum(encoded * weights.unsqueeze(-1), dim=1)
        return context, weights


class LSTMTemporalVAE(nn.Module):
    """One-layer 64-unit LSTM VAE with temporal attention and 16-D latent space."""

    def __init__(
        self,
        input_size: int,
        sequence_length: int = SEQUENCE_LENGTH,
        hidden_size: int = HIDDEN_SIZE,
        latent_size: int = LATENT_SIZE,
    ) -> None:
        super().__init__()
        self.input_size = input_size
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.latent_size = latent_size

        self.encoder = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.attention = TemporalAttention(hidden_size)
        self.to_mean = nn.Linear(hidden_size, latent_size)
        self.to_log_variance = nn.Linear(hidden_size, latent_size)
        self.latent_to_hidden = nn.Linear(latent_size, hidden_size)
        self.decoder = nn.LSTM(hidden_size, hidden_size, batch_first=True)
        self.output_projection = nn.Linear(hidden_size, input_size)

    @staticmethod
    def reparameterize(mean: Tensor, log_variance: Tensor) -> Tensor:
        if not mean.requires_grad:
            return mean
        standard_deviation = torch.exp(0.5 * log_variance)
        return mean + torch.randn_like(standard_deviation) * standard_deviation

    def forward(self, inputs: Tensor) -> TemporalVAEOutput:
        encoded, _ = self.encoder(inputs)
        context, attention_weights = self.attention(encoded)
        mean = self.to_mean(context)
        log_variance = torch.clamp(self.to_log_variance(context), min=-10.0, max=6.0)
        latent = self.reparameterize(mean, log_variance)
        hidden = self.latent_to_hidden(latent).unsqueeze(1).repeat(1, self.sequence_length, 1)
        decoded, _ = self.decoder(hidden)
        reconstruction = self.output_projection(decoded)
        return TemporalVAEOutput(reconstruction, mean, log_variance, attention_weights)

    def anomaly_components(self, inputs: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        self.eval()
        with torch.no_grad():
            output = self.forward(inputs)
            reconstruction_error = F.mse_loss(output.reconstruction, inputs, reduction="none").mean(dim=(1, 2))
            latent_uncertainty = torch.exp(output.log_variance).mean(dim=1)
        return reconstruction_error, latent_uncertainty, output.attention_weights


def temporal_vae_loss(output: TemporalVAEOutput, target: Tensor, beta: float = 0.001) -> Tensor:
    reconstruction = F.mse_loss(output.reconstruction, target)
    kl_divergence = -0.5 * torch.mean(
        1.0 + output.log_variance - output.mean.pow(2) - output.log_variance.exp()
    )
    return reconstruction + beta * kl_divergence


def load_temporal_vae(checkpoint: Path, input_size: int) -> LSTMTemporalVAE:
    model = LSTMTemporalVAE(input_size=input_size)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model

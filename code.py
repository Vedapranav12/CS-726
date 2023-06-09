# -*- coding: utf-8 -*-
"""code.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12CvYcFad3Sr_9KM28TMpv5fXrJPo_WVg
"""

import numpy as np
import torch
import torchvision
from torch import nn
from torch.nn import functional as F

from tqdm.notebook import tqdm

# Define the diffusion function
class DiffusionFunction(nn.Module):
    def __init__(self, dims):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dims+1, dims),
            nn.ReLU(),
            nn.Linear(dims, dims),
            nn.Tanh()
        )
        self.dims = dims

    def forward(self, xt, t, noise):
        noise_t = noise * torch.sqrt(1 - t)
        xt_prime = xt + noise_t
        ft = self.net(torch.cat([xt_prime, t.unsqueeze(0)], dim=0))
        xt_next = xt_prime + (1 - t) * ft
        return xt_next

# Define the Diffusion SCM
class DiffSCM(nn.Module):
    def __init__(self, dims):
        super().__init__()
        self.diffusion = DiffusionFunction(dims)

        self.mean = nn.Linear(dims, dims)
        self.var = nn.Sequential(
            nn.Linear(dims, dims),
            nn.Softplus()
        )
        self.dims = dims

    def sample(self, n_samples, device):
        noise = torch.randn(n_samples, self.dims).to(device)
        x0 = torch.randn(n_samples, self.dims).to(device)
        t = torch.linspace(0, 1, n_samples).to(device)

        xt = x0
        for i in range(n_samples):
            xt[i, :] = self.diffusion(xt[i, :], t[i], noise[i, :])
        return xt

    def forward(self, x):
        t = torch.rand(x.shape[0], 1).to(x.device)
        xt = self.sample(x.shape[0], x.device)

        mu = self.mean(xt)
        sigma = self.var(xt)
        eps = torch.randn(x.shape).to(x.device)
        x_prime = mu + sigma * eps

        x_tilde = (1 - t) * x + t * x_prime
        return x_tilde

# Define the training loop
def train_diff_scm(model, data_loader, optimizer, device):
    model.train()
    losses = []
    for batch_idx, (x, _) in tqdm(enumerate(data_loader)):
        x = x.to(device)

        optimizer.zero_grad()
        batch_size = x.shape[0]
        x_bt = torch.reshape(x, (batch_size, -1))
        x_tilde = model(x_bt)
        loss = F.mse_loss(x_tilde, x_bt)
        losses.append(loss.item())

        loss.backward()
        optimizer.step()

    return np.mean(losses)

# Set up the training data and model
train_data = torchvision.datasets.MNIST(
    root='.',
    train=True,
    transform=torchvision.transforms.ToTensor(),
    download=True
)
train_loader = torch.utils.data.DataLoader(train_data, batch_size=128, shuffle=True)
diff_scm = DiffSCM(784).to('cuda')

# Set up the optimizer and train the model
optimizer = torch.optim.Adam(diff_scm.parameters(), lr=1e-3)
for epoch in range(10):
    loss = train_diff_scm(diff_scm, train_loader, optimizer, 'cuda')
    print(f'Epoch {epoch+1} Loss: {loss:.4f}')

# Save the trained model
torch.save(diff_scm.state_dict(), 'diff_scm_mnist_model.pth')

train_input = train_data.train_data.view(-1, 1, 28, 28).float()
train_target = train_data.train_labels
test_input = train_data.test_data.view(-1, 1, 28, 28).float()
test_target = train_data.test_labels

train_input[0]

import matplotlib.pyplot as plt

my_img = train_input[200]

plt.imshow(my_img.permute(1, 2, 0) )

cf = diff_scm(torch.reshape(torch.tensor(my_img), (-1, 784)).to('cuda'))

cf = torch.reshape(cf, (28, 28, 1))
plt.imshow(cf.detach().cpu().numpy())

torch.mean(torch.abs(cf - my_img.to('cuda'
)))

plt.imshow(np.zeros((28, 28, 1)))


# swarm_sim.py
import torch
import torch.nn as nn
import torch.optim as optim


# =========================================================
# 1. Neural Lyapunov Function (Value Function Surrogate)
# =========================================================

class NeuralLyapunov(nn.Module):
    def __init__(self, state_dim, hidden=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 1),
            nn.Softplus()   # V(x) >= 0
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


# =========================================================
# 2. Mode Policies (Switched Control Set)
# =========================================================

class ModePolicy:
    def __init__(self, A, bias=0.0):
        self.A = A
        self.bias = bias

    def __call__(self, x):
        return torch.tanh(x @ self.A + self.bias)


# =========================================================
# 3. Switched Policy Graph
# =========================================================

class PolicyGraph:
    def __init__(self, modes):
        self.modes = modes

    def select_mode(self, x, V):
        best_mode = None
        best_score = float("inf")

        for m in self.modes:
            u = m(x)
            score = V(x + u).item()

            if score < best_score:
                best_score = score
                best_mode = m

        return best_mode


# =========================================================
# 4. Swarm Dynamics (GPU-ready tensor model)
# =========================================================

class Swarm:
    def __init__(self, n_agents, state_dim):
        self.n = n_agents
        self.d = state_dim

        # learned interaction graph
        self.A = nn.Parameter(torch.randn(n_agents, n_agents) * 0.1)

    def step(self, X, U):
        interaction = self.A @ X
        return X + U + 0.05 * interaction


# =========================================================
# 5. Adversarial Disturbance
# =========================================================

class Adversary:
    def __init__(self, strength=0.05):
        self.strength = strength

    def __call__(self, X):
        return X + self.strength * torch.randn_like(X)


# =========================================================
# 6. Switched Lyapunov System
# =========================================================

class SwitchedLyapunovSystem:
    def __init__(self, n_agents=32, state_dim=4):

        self.n = n_agents
        self.d = state_dim

        self.V = NeuralLyapunov(state_dim)

        # two control modes
        self.modes = [
            ModePolicy(torch.randn(state_dim, state_dim) * 0.1),
            ModePolicy(torch.randn(state_dim, state_dim) * 0.2),
        ]

        self.graph = PolicyGraph(self.modes)
        self.swarm = Swarm(n_agents, state_dim)
        self.adversary = Adversary()

        self.opt = optim.Adam(
            list(self.V.parameters()) + [self.swarm.A],
            lr=1e-3
        )

    # -----------------------------------------------------
    # Lyapunov stability surrogate loss
    # -----------------------------------------------------
    def lyapunov_loss(self, X, X_next):
        Vx = self.V(X)
        Vn = self.V(X_next)

        # enforce decrease condition
        return torch.relu(Vn - Vx + 0.01 * Vx).mean()

    # -----------------------------------------------------
    # one simulation step
    # -----------------------------------------------------
    def step(self, X):

        X = self.adversary(X)

        U = []
        for i in range(self.n):
            x = X[i]
            mode = self.graph.select_mode(x, self.V)
            u = mode(x)
            U.append(u)

        U = torch.stack(U)

        return self.swarm.step(X, U)

    # -----------------------------------------------------
    # training step
    # -----------------------------------------------------
    def train_step(self, X):
        X_next = self.step(X)

        loss = self.lyapunov_loss(X, X_next)

        self.opt.zero_grad()
        loss.backward()
        self.opt.step()

        return loss.item()


# =========================================================
# 7. Run Simulation
# =========================================================

def main():
    torch.manual_seed(0)

    system = SwitchedLyapunovSystem(
        n_agents=32,
        state_dim=4
    )

    X = torch.randn(32, 4)

    for step in range(200):
        loss = system.train_step(X)
        X = system.step(X)

        if step % 20 == 0:
            V = system.V(X).mean().item()
            print(f"step {step:03d} | loss={loss:.6f} | V={V:.6f}")


if __name__ == "__main__":
    main()
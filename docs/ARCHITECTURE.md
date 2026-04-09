# Project Architecture

This document describes the high-level architecture of the **Secure Federated Learning** system.

## Overview

The system is designed as a decentralized research platform that combines **Federated Learning (FL)** with **Blockchain** technology to ensure data privacy, model integrity, and participant accountability.

```mermaid
graph TD
    subgraph "Clients (P1 ... PN)"
        C1[Local Training]
        C2[DP Noise Injection]
        C3[Secure Sharing]
    end

    subgraph "Blockchain Layer"
        BC[Distributed Ledger]
        SC[Smart Contracts]
        RM[Reputation Manager]
    end

    subgraph "Server Aggregation"
        SA[Secure Aggregator]
        GM[Global Model]
        CA[Proof-of-Accuracy Consensus]
    end

    C1 --> C2
    C2 --> C3
    C3 -- Update Shares --> SA
    SA -- Reconstructed Aggregate --> GM
    SC -- Validation --> BC
    GM -- Model Broadcast --> CA
    CA -- Approved Update --> GM
    BC -- Log Audit Trail --> SC
```

## Core Components

### 1. Federated Learning Lifecycle
*   **Initialization**: The global server initializes a base model (e.g., Simple MLP for MNIST) and broadcasts it to all participants.
*   **Local Training**: Each client trains the model on its private dataset.
*   **Privacy Guard**: Before submission, updates are processed via **Differential Privacy (DP)** to prevent information leakage.
*   **Aggregation**: The server collects updates and computes a new global model using robust strategies (e.g., Median or Trimmed Mean).

### 2. Blockchain Integration
*   **Immutable Ledger**: Every model update, transaction, and validation result is recorded on an in-memory blockchain.
*   **Consensus (Proof-of-Work)**: Mining ensures the integrity of the chain and prevents tampering.
*   **Smart Contracts**:
    *   **Validation Contract**: Checks updates for anomalies (L2-norm clipping, cosine similarity against the median).
    *   **Aggregation Contract**: Manages the secure collection of shares.

### 3. Reputation & Security
*   **Reputation System**: Participants start with a base score. Valid updates earn rewards, while malicious or low-quality updates are penalized.
*   **Blacklisting**: Clients whose reputation falls below a threshold are blocked from participating in future rounds.
*   **Consensus (Proof-of-Accuracy)**: A supermajority of "validator" nodes must vote to accept a global update based on their own local performance validation.

## Dashboard Visualization

The `dashboard/index.html` file serves as a **standalone research visualizer**. It simulates the entire BCFL process (Blockchain Federated Learning) in the browser to demonstrate:
*   Real-time accuracy convergence.
*   Malicious node detection.
*   Ledger block generation.
*   Reputation leaderboard updates.

> [!NOTE]
> The dashboard is a client-side simulation (Mocked JS) and does not interact directly with the Python backend. It is intended for presentation and educational purposes.

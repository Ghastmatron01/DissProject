# UK Housing Market Simulation: Rule-Based vs. LLM Agent-Based Modeling

## Overview

This repository contains a Python-based Agent-Based Model (ABM) simulating the UK residential housing market. The project investigates barriers preventing first-time buyers from accessing homeownership, focusing on the "rent trap." It enables comparison between frictionless mathematical agents and LLM-augmented agents that simulate human-like reasoning and risk aversion.

## Key Features
- **Dual Cognitive Engine:**
  - **Rule-Based Agents:** Operate as mathematical optimisers.
  - **LLM-Augmented Agents (ReAct):** Use natural language reasoning (via Llama 3.2) to simulate bounded rationality and economic anxiety.
- **Realistic Data:** Integrates HM Land Registry, ONS earnings, and other UK datasets.
- **Customisable Simulation:** Configure agent count, time steps, and simulation mode.
- **Automated Reporting:** Generates statistical reports and graphs comparing model output to UK benchmarks.
- **Comprehensive Testing:** Includes unit, integration, and boundary tests for reliability.

---

## Prerequisites
- **Python 3.9+** (Tested on Python 3.10+)
- **Ollama** (for running local Large Language Models)
- **Llama 3.2** model (downloaded via Ollama)
- **Git** (for cloning the repository)
- **Git LFS** (for downloading large datasets)

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/uk-housing-abm.git
cd Dissertation
```

### 2. Set Up Python Virtual Environment
**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```
**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Ollama and Llama 3.2
- Download Ollama: [https://ollama.com/download](https://ollama.com/download)
- Install and run Ollama following on-screen prompts.
- Download the Llama 3.2 model:
```bash
ollama run llama3.2
```
- Once the model is downloaded and you see a prompt, type `/bye` to exit.

### 5. Download Datasets with Git LFS
This project uses [Git Large File Storage (LFS)](https://git-lfs.com/) to manage large datasets (e.g., CSV, XLSX files).

- **Install Git LFS:**
  ```bash
  git lfs install
  ```
- **Clone the repository (if not already done):**
  ```bash
  git clone https://github.com/yourusername/uk-housing-abm.git
  cd Dissertation
  ```
- **Git LFS will automatically download all large files tracked in the repository.**

> **Note:** If you clone the repository without Git LFS installed, you will only get pointer files instead of the actual datasets. Install Git LFS and run `git lfs pull` to fetch the data.

### 6. Prepare Data (if adding your own)
- Place required CSV/XLSX data files (e.g., HM Land Registry, ONS earnings) in the `data/` directory.
- The simulation will automatically filter and clean data at runtime.

---

## Running the Simulation

### 1. Execute the Simulation
```bash
python run_simulation.py
```
- Select simulation mode (Rule-Based or LLM) and configure parameters as prompted.
- Results are saved as CSV in the `results/` folder (e.g., `results/simulation_YYYYMMDD_HHMMSS.csv`).

**Note:** LLM-augmented simulations are computationally intensive and may take hours for large runs.

### 2. Generate Reports and Graphs
```bash
python simulation_report.py
```
- Reads the latest results CSV and generates statistical reports and graphs in `results/graphs/`.

---

## Testing and Validation

This project uses `pytest` for comprehensive testing (unit, integration, boundary):
```bash
pytest
```
- Some tests requiring large datasets or external APIs may be skipped for speed.

---

## Troubleshooting
- **Ollama/Llama errors:** Ensure Ollama is running and the Llama 3.2 model is downloaded.
- **Missing data:** Verify all required data files are in the `data/` directory and that Git LFS is installed.
- **Dependency issues:** Reinstall requirements with `pip install -r requirements.txt`.
- **Long runtimes:** Use fewer agents or shorter time steps for testing.

---

## Project Structure
- `run_simulation.py` — Main simulation entry point
- `simulation_report.py` — Generates reports and graphs
- `Agents/` — Agent logic and cognitive engines
- `Algorithms/` — Data extraction, fault modelling, and algorithms
- `Environment/` — Market, housing, and mortgage environment
- `Financial/` — Debt, savings, and expense management
- `data/` — All required datasets
- `results/` — Simulation outputs and graphs
- `tests/` — Test suite and test plan

---

## Support & Contact
For questions, issues, or contributions, please open an issue on GitHub or contact the project maintainer.

---


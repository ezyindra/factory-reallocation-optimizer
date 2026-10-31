# Factory Reallocation & Optimization System

A Python-based decision-support system that analyzes product demand, evaluates factory capacity, and recommends balanced factory allocations using mathematical optimization.

Built around the Nassau Candy Distributor dataset, this project explores how a distributor could evaluate production capacity and respond to changing operational scenarios.

## Overview

The system transforms historical sales data into product-market demand, allocates that demand across a configurable factory network, validates the resulting allocations, and presents operational insights through an interactive Streamlit dashboard.

The optimization engine uses **Google OR-Tools CP-SAT** to minimize maximum factory utilization while satisfying demand and respecting factory capacity and product eligibility constraints.

## Key Features

- **Demand Analysis:** Aggregates product demand across countries and regions.
- **Factory Configuration:** Defines factory capacities, availability, and supported products through JSON configuration.
- **Optimization Engine:** Uses OR-Tools CP-SAT to generate capacity-constrained factory allocations.
- **Allocation Validation:** Independently checks demand reconciliation, factory capacity, and factory eligibility.
- **Scenario Analysis:** Evaluates factory shutdowns, capacity reductions, and capacity expansions.
- **Recommendation Engine:** Generates operational recommendations based on network capacity and factory utilization.
- **Interactive Dashboard:** Explores demand, factory performance, allocations, scenarios, and validation results.
- **Automated Testing:** Uses pytest to verify optimization and validation behavior.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Data processing | Pandas, NumPy |
| Optimization | Google OR-Tools CP-SAT |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Testing | Pytest |

## Project Architecture

```text
factory-reallocation-optimizer/
│
├── app.py
│
├── config/
│   └── factory_assumptions.json
│
├── data/
│   ├── raw/
│   │   └── Nassau Candy Distributor.csv
│   │
│   └── processed/
│
├── src/
│   ├── data_loader.py
│   ├── date_audit.py
│   ├── date_validation.py
│   ├── preprocessing.py
│   ├── demand_analysis.py
│   ├── factory_config.py
│   ├── optimization_engine.py
│   ├── allocation_validator.py
│   ├── recommendation_engine.py
│   ├── scenario_simulator.py
│   └── scenario_optimizer.py
│
├── tests/
│   ├── test_optimization_engine.py
│   └── test_allocation_validator.py
│
├── requirements.txt
└── README.md
```

## Dataset

The project uses the Nassau Candy Distributor dataset containing transaction-level sales information.

Key fields include:

- Order ID and Order Date
- Product ID and Product Name
- Country/Region and Region
- Units and Sales
- Cost and Gross Profit
- Ship Date and Ship Mode

### Dataset Summary

| Metric | Value |
|---|---:|
| Transaction records | 10,194 |
| Products | 15 |
| Cities | 542 |
| State/Provinces | 59 |
| Total units sold | 38,654 |
| Total sales | $141,783.63 |
| Gross profit | $93,442.80 |

The dataset is used to derive product-market demand for the allocation model.

## Optimization Methodology

The optimization engine groups demand by:

- Product ID
- Product Name
- Country/Region
- Region

It then creates allocation variables for eligible factories.

### Objective

Minimize the maximum utilization across enabled factories.

\[
\min U_{\max}
\]

Subject to:

**1. Demand fulfillment**

\[
\sum_f x_{f,d}=D_d
\]

**2. Factory capacity**

\[
\sum_d x_{f,d}\leq C_f
\]

**3. Factory eligibility**

Only enabled factories that support a product can receive its allocation.

**4. Non-negative allocations**

\[
x_{f,d}\geq 0
\]

Where:

- \(x_{f,d}\) = units allocated by factory \(f\) to demand bucket \(d\)
- \(D_d\) = demand for bucket \(d\)
- \(C_f\) = available capacity of factory \(f\)
- \(U_{\max}\) = maximum factory utilization

The CP-SAT solver works with integer allocation variables and integer-scaled utilization constraints.

## Illustrative Factory Network

The factory configuration is maintained in:

`config/factory_assumptions.json`

| Factory | Capacity |
|---|---:|
| Factory North | 16,000 |
| Factory Central | 14,000 |
| Factory South | 12,000 |
| **Total** | **42,000** |

These factory profiles are simulation assumptions created for this project. They are not verified Nassau Candy operational records.

### Baseline Optimization Results

| Metric | Result |
|---|---:|
| Total demand | 38,654 units |
| Total capacity | 42,000 units |
| Spare capacity | 3,346 units |
| Network utilization | 92.03% |
| Solver status | OPTIMAL |

The baseline allocation balances utilization across the three illustrative factories.

## Scenario Analysis

The system evaluates alternative factory-network configurations.

| Scenario | Capacity | Spare Capacity | Utilization |
|---|---:|---:|---:|
| Baseline | 42,000 | 3,346 | 92.03% |
| Factory North shutdown | 26,000 | -12,654 | Infeasible |
| Factory Central capacity reduction (-20%) | 39,200 | 546 | 98.61% |
| All factories capacity expansion (+10%) | 46,200 | 7,546 | 83.67% |

Each feasible scenario is evaluated using the optimization engine. Scenarios with insufficient total capacity are rejected before optimization.

## Interactive Dashboard

The Streamlit application provides six main sections:

1. **Overview** – Network demand, capacity, spare capacity, and utilization.
2. **Factory Analysis** – Factory-level capacity and utilization insights.
3. **Allocation Explorer** – Explore optimized product and market allocations.
4. **Scenario Analysis** – Change factory capacity and run new optimization scenarios.
5. **Recommendations** – Review operational recommendations.
6. **Validation** – Inspect independent allocation validation results.

## Installation

### Prerequisites

- Python 3.10 or later
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/ezyindra/factory-reallocation-optimizer.git
cd factory-reallocation-optimizer
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Add the dataset

Place the original dataset at:

```text
data/raw/Nassau Candy Distributor.csv
```

The raw dataset is not included in the repository.

## Running the Project

Run the data preparation and analysis modules as required:

```bash
python -m src.preprocessing
python -m src.demand_analysis
python -m src.optimization_engine
python -m src.allocation_validator
python -m src.recommendation_engine
python -m src.scenario_optimizer
```

Launch the interactive dashboard:

```bash
python -m streamlit run app.py
```

Streamlit will provide a local URL in the terminal.

## Running Automated Tests

Run the complete test suite:

```bash
python -m pytest -v
```

Run individual test modules:

```bash
python -m pytest tests/test_optimization_engine.py -v
python -m pytest tests/test_allocation_validator.py -v
```

The current test suite covers demand aggregation, allocation constraints, factory eligibility, capacity validation, and invalid allocation scenarios.

## Important Assumptions and Limitations

- Factory capacities and factory profiles are illustrative simulation assumptions.
- The dataset does not provide verified factory locations, production capacities, or factory-specific production costs.
- Actual transportation rates, route distances, and logistics costs are not available in the dataset.
- Therefore, this implementation focuses on factory allocation and capacity optimization, not real-world shipping-route or transportation-cost optimization.
- Recorded order and ship dates contain anomalous differences and should not be treated as verified delivery lead times.
- Optimization results represent the configured simulation scenario and should not be interpreted as actual operational recommendations for Nassau Candy without validated factory and logistics data.

## Future Improvements

- Incorporate verified factory locations and production capacities.
- Add transportation costs and route-distance data.
- Extend the optimization model to include shipping and production costs.
- Introduce demand forecasting using historical sales data.
- Add sensitivity analysis and more complex operational scenarios.
- Expand automated testing and model performance reporting.

## Author

Developed as part of a Machine Learning internship project.

**GitHub:** [@ezyindra](https://github.com/ezyindra)

---

*This project is an analytical and optimization prototype built for operational decision-support experimentation.*

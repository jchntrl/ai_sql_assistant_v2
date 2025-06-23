# Agent Handoff Flowchart

This flowchart shows the detailed agent handoff patterns and workflow in the SnowGPT application.

```mermaid
flowchart TD
    A[User Input] --> B[Routing Agent]
    
    B --> C{Routing Decision}
    
    C -->|Needs Clarification| D[Ask Clarifying Questions]
    D --> E[User Response]
    E --> B
    
    C -->|SQL Query Request| F[Dashboard Confirmation?]
    F -->|No| G[SQL Query Agent Path]
    F -->|Yes| H{User Confirms Dashboard?}
    
    H -->|No| G
    H -->|Yes| I[Dashboard Agent Path]
    
    C -->|Dashboard Request| H
    
    %% SQL Query Agent Path
    G --> J[Database SME Agent]
    J --> K{Sufficient Context?}
    K -->|No| L[Return Explanation to User]
    L --> M[End]
    
    K -->|Yes| N[SQL Query Builder Agent]
    N --> O[Auto-validate SQL]
    O --> P{SQL Valid?}
    
    P -->|No + Force Validator| Q[SQL Validator Agent]
    P -->|No + No Validator| R[Return Error to User]
    R --> M
    
    Q --> S[Retry Loop<br/>Max 3 attempts]
    S --> T{Validation Success?}
    T -->|No| U[Handoff to SQL Builder<br/>with Error Context]
    U --> N
    T -->|Yes| V[Execute SQL Query]
    
    P -->|Yes| V
    V --> W[Convert Data<br/>Decimal to Float]
    W --> X[Display Results Table]
    X --> Y[Chart Generator Agent<br/>Single Query]
    Y --> Z{Visualization Needed?}
    Z -->|Yes| AA[Generate & Execute Chart]
    Z -->|No| AB[Show Table Only]
    AA --> M
    AB --> M
    
    %% Dashboard Agent Path
    I --> AC[Dashboard Designer Agent]
    AC --> AD{Sufficient Context?}
    AD -->|No| AE[Return Clarification Questions]
    AE --> M
    
    AD -->|Yes| AF[Generate 5 Visualizations<br/>with SQL Queries]
    AF --> AG[For Each Visualization]
    AG --> AH[Execute SQL Query]
    AH --> AI[Convert Data<br/>Decimal to Float]
    AI --> AJ[Chart Generator Agent<br/>Dashboard Mode]
    AJ --> AK[Generate Chart Code]
    AK --> AL{More Visualizations?}
    AL -->|Yes| AG
    AL -->|No| AM[Render Dashboard Layout<br/>2x2 Grid + Optional 5th]
    AM --> M
    
    %% Styling
    classDef agentBox fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef decisionBox fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef userBox fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef endBox fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    
    class B,J,N,Q,Y,AC,AJ agentBox
    class C,F,H,K,P,T,Z,AD,AL decisionBox
    class A,D,E,L,AE userBox
    class M endBox
```

## Agent Descriptions

### Core Agents

1. **Routing Agent** - Analyzes user requests and determines the appropriate specialized agent
2. **Database SME Agent** - Analyzes database context and user requirements
3. **SQL Query Builder Agent** - Generates SQL queries from natural language
4. **SQL Validator Agent** - Validates and refines SQL queries (optional)
5. **Chart Generator Agent** - Creates visualization code for both single queries and dashboards
6. **Dashboard Designer Agent** - Creates comprehensive multi-panel dashboards

### Key Decision Points

- **Dashboard Confirmation**: Routing agent asks for explicit confirmation before dashboard creation
- **Sufficient Context**: SME and Dashboard agents check if enough information is available
- **SQL Validation**: Multiple validation paths with retry mechanisms
- **Visualization Need**: Chart agent determines if visualization is appropriate for the data

### Retry Mechanisms

- **SQL Validation Loop**: Up to 3 attempts with error context feedback
- **Context Building**: Routing agent can loop indefinitely until clear handoff

### Chart Generation Modes

- **Single Query Mode**: After SQL execution, generates one chart
- **Dashboard Mode**: Generates multiple charts for dashboard layout
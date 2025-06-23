# Session State Management Flowchart

This flowchart shows the session state management and lifecycle in the SnowGPT application.

```mermaid
flowchart TD
    A[App Initialization] --> B[Check Database/Schema Selection]
    B --> C{Context Changed?}
    
    C -->|Yes| D[Reset Session State]
    C -->|No| E[Preserve Session State]
    
    D --> F[Clear Messages]
    D --> G[Reset Router Counter to 0]
    D --> H[Reset Handoff to 'user']
    D --> I[Clear Routing Data]
    D --> J[Clear User Input History]
    
    F --> K[Update Current Context]
    G --> K
    H --> K
    I --> K
    J --> K
    
    E --> L[Initialize Missing State]
    K --> L
    
    L --> M[Set Default Values]
    M --> N{Router Counter exists?}
    N -->|No| O[router_counter = 0]
    N -->|Yes| P{Handoff exists?}
    
    O --> P
    P -->|No| Q[handoff = 'user']
    P -->|Yes| R{Routing exists?}
    
    Q --> R
    R -->|No| S[routing = None]
    R -->|Yes| T{User Input History exists?}
    
    S --> T
    T -->|No| U[user_input_history = empty list]
    T -->|Yes| V{Messages exist?}
    
    U --> V
    V -->|No| W[messages = empty list]
    V -->|Yes| X[State Ready for User Input]
    
    W --> X
    
    %% User Input Processing
    X --> Y[User Provides Input]
    Y --> Z{Handoff State?}
    
    Z -->|'user'| AA{Router Counter = 0?}
    Z -->|'sql_query_agent'| BB[Process SQL Agent]
    Z -->|'dashboard_agent'| CC[Process Dashboard Agent]
    
    %% First Time Routing
    AA -->|Yes| DD[Increment Router Counter]
    DD --> EE[Add to User Input History]
    EE --> FF[Execute Routing Agent]
    FF --> GG{Routing Result?}
    
    GG -->|handoff = 'user'| HH[Add Routing Message to History]
    GG -->|handoff = 'sql_query_agent'| II[Set Handoff State]
    GG -->|handoff = 'dashboard_agent'| II
    
    HH --> JJ[Store Routing Questions]
    JJ --> KK[Rerun App]
    KK --> X
    
    %% Follow-up Routing
    AA -->|No| LL[Add to User Input History]
    LL --> MM[Build Context from History]
    MM --> FF
    
    %% Agent Processing
    II --> NN[Store Routing Data]
    NN --> OO[Process Agent Request]
    
    BB --> OO
    CC --> OO
    
    OO --> PP[Agent Execution Complete]
    PP --> QQ[Add Agent Response to Messages]
    QQ --> RR[Clean Up Temporary State]
    
    RR --> SS[Delete Router Counter]
    RR --> TT[Reset Handoff to 'user']
    RR --> UU[Delete Routing Data]
    RR --> VV[Delete User Input History]
    
    SS --> WW[State Reset Complete]
    TT --> WW
    UU --> WW
    VV --> WW
    
    WW --> X
    
    %% Context Change Detection
    XX[Database/Schema Selection Change] --> YY[Log Context Change]
    YY --> ZZ[Clear Relevant Session Keys]
    ZZ --> AAA{Key Exists?}
    AAA -->|messages| BBB[Delete messages]
    AAA -->|router_counter| CCC[Delete router_counter]
    AAA -->|handoff| DDD[Delete handoff]
    AAA -->|routing| EEE[Delete routing]
    AAA -->|user_input_history| FFF[Delete user_input_history]
    
    BBB --> GGG[Update Current Context Tracking]
    CCC --> GGG
    DDD --> GGG
    EEE --> GGG
    FFF --> GGG
    
    GGG --> HHH[Reconnect to Database]
    HHH --> X
    
    %% Styling
    classDef initBox fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef stateBox fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef processBox fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef decisionBox fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef cleanupBox fill:#ffebee,stroke:#c62828,stroke-width:2px
    
    class A,B,L,M,X,XX,YY,HHH initBox
    class D,F,G,H,I,J,K,O,Q,S,U,W,NN,QQ stateBox
    class DD,EE,FF,LL,MM,OO,PP,ZZ,BBB,CCC,DDD,EEE,FFF,GGG processBox
    class C,N,P,R,T,V,Z,AA,GG,AAA decisionBox
    class RR,SS,TT,UU,VV,WW cleanupBox
```

## Session State Variables

### Core State Variables

| Variable | Type | Purpose | Reset Conditions |
|----------|------|---------|------------------|
| `messages` | List | Chat history storage | Database/schema change |
| `router_counter` | Int | Routing iteration tracking | Agent completion, context change |
| `handoff` | String | Current workflow state | Agent completion |
| `routing` | Object | Routing agent output | Agent completion, context change |
| `user_input_history` | List | Multi-turn context building | Agent completion, context change |
| `current_db` | String | Database context tracking | Never (persistent) |
| `current_schema` | String | Schema context tracking | Never (persistent) |

### State Values

#### Handoff States
- `'user'` - Waiting for user input or routing
- `'sql_query_agent'` - Processing SQL query request
- `'dashboard_agent'` - Processing dashboard request

#### Router Counter Logic
- `0` - First user interaction, direct routing
- `>0` - Follow-up interaction, context accumulation

## State Lifecycle Events

### Initialization
1. Check for context changes (database/schema)
2. Reset state if context changed
3. Initialize missing state variables with defaults
4. Prepare for user input

### User Interaction Cycle
1. Capture user input
2. Route based on current handoff state
3. Process through appropriate agent
4. Update messages and state
5. Clean up temporary state
6. Reset to user state

### Context Change Handling
1. Detect database/schema selection change
2. Log context change event
3. Clear conversation-specific state
4. Update persistent context tracking
5. Reconnect to new database context
6. Resume normal operation

### State Cleanup
- **Temporary State**: Cleared after each agent completion
- **Persistent State**: Maintained across interactions unless context changes
- **Context State**: Only updated on database/schema changes
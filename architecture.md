# Deep Research Architecture

## End-to-End Execution Flow

This sequence diagram illustrates the complete flow of a Deep Research task, highlighting the recursive "Host Query" mechanism where the Researcher agent asks the Host (Gemini CLI) to perform actions.

```mermaid
sequenceDiagram
    actor User
    participant Host as Gemini CLI (Host)
    participant Server as MCP Server
    participant Orch as Orchestrator
    participant Plan as Planner Agent
    participant Res as Researcher Agent
    participant Tool as AskHostTool
    participant Write as Writer Agent
    participant Rev as Reviewer Agent

    User->>Host: "Research X"
    Host->>Server: perform_deep_research(topic="X")
    Server->>Orch: start_research()
    
    %% Planning Phase
    Orch->>Plan: generate_plan(topic)
    Plan-->>Orch: Research Plan

    %% Research Phase (Loop)
    loop For each step in Plan
        Orch->>Res: execute_step(step)
        
        %% Recursive Host Query
        alt Needs Info/Search
            Res->>Tool: ask_host_for_info("Search for Y")
            Tool->>Host: Sampling Request ("Search for Y")
            Host->>Host: Execute Google Search / Terminal
            Host-->>Tool: Search Results / Info
            Tool-->>Res: Info
        end
        
        Res-->>Orch: Step Findings
    end

    %% Writing Phase
    Orch->>Write: write_report(findings)
    Write-->>Orch: Draft Report

    %% Review Phase (Cycle 3)
    Orch->>Rev: review_report(draft)
    Rev-->>Orch: Feedback (Critique)
    
    alt Feedback exists
        Orch->>Write: revise_report(draft, feedback)
        Write-->>Orch: Final Report
    end

    Orch-->>Server: Final Report
    Server-->>Host: Result
    Host-->>User: Display Report
```

## Component Interaction

```mermaid
graph TD
    User[User] <--> Host[Gemini CLI Host]
    Host <-->|MCP Protocol| Server[Deep Research Server]
    
    subgraph "Deep Research Server"
        Server --> Orch[Orchestrator]
        Orch --> Planner[Planner Agent]
        Orch --> Researcher[Researcher Agent]
        Orch --> Writer[Writer Agent]
        Orch --> Reviewer[Reviewer Agent]
    end
    
    subgraph "Recursive Loop"
        Researcher -->|Uses| AskHostTool
        AskHostTool -->|Sampling Request| Host
        Host -->|Executes| GoogleSearch[Google Search]
        Host -->|Executes| Terminal[Local Terminal]
    end
```

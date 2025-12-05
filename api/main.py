import json
from orchestrator import AdvisorOrchestrator

def main():
    print("=== Czech Political/Economic Advisor MVP ===")
    
    # Example Input from the prompt
    input_plan = "We will abolish subsidies for renewable energy sources to save 20 billion CZK."
    
    print(f"\nUser Input: \"{input_plan}\"\n")
    
    orchestrator = AdvisorOrchestrator()
    result = orchestrator.analyze_plan(input_plan)
    
    print("\n=== Analysis Result ===\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

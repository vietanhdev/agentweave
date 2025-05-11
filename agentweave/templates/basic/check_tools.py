#!/usr/bin/env python3
"""
Quick script to check registered tools.
"""

from tools.registry import get_tools_schema


def main():
    """List all registered tools."""
    print("Checking registered tools...")
    tools = get_tools_schema()

    print(f"\nFound {len(tools)} tools:")
    for i, tool in enumerate(tools):
        print(f"{i + 1}. {tool['name']} - {tool['description'][:50]}...")
        print(f"   Enabled: {tool['enabled']}")

    # Check if calculator is registered
    calculator = next((t for t in tools if t["name"] == "calculator"), None)
    if calculator:
        print("\nCalculator tool is registered!")
    else:
        print("\nCalculator tool is NOT registered!")

        # Print all loaded module names
        print("\nLoaded tool modules:")
        import sys

        for module_name in sys.modules:
            if module_name.startswith("tools.") and not module_name.startswith("tools.registry"):
                print(f"- {module_name}")


if __name__ == "__main__":
    main()

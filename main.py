import time
import traceback
from config import OPENAI_API_KEY, BROWSER_OPTIONS, BROWSER_CONNECTION
from browser_setup import initialize_browser, close_browser
from browser_controller import VirtualBrowserController
from agent_tools import create_browser_tools
from agent import create_agent
from chrome_launcher import launch_chrome_with_debugging

def main():
    """Main entry point for the browser automation agent."""
    try:
        # Step 1: Automatically launch Chrome with remote debugging if needed
        if BROWSER_CONNECTION.get("use_existing", False):
            port = 9222  # Default port
            # Extract port from cdp_endpoint if specified
            if "cdp_endpoint" in BROWSER_CONNECTION:
                try:
                    endpoint = BROWSER_CONNECTION["cdp_endpoint"]
                    port = int(endpoint.split(":")[-1])
                except (ValueError, IndexError):
                    pass

            print("Ensuring Chrome is running with remote debugging...")
            chrome_launched = launch_chrome_with_debugging(port)
            if not chrome_launched and not BROWSER_CONNECTION.get("fallback_to_new", True):
                print("❌ Failed to launch Chrome with debugging and fallback is disabled")
                return

        # Step 2: Initialize browser with connection options
        print("Initializing browser...")
        playwright, browser, page = initialize_browser(BROWSER_OPTIONS, BROWSER_CONNECTION)

        # Track connection state
        using_connected_browser = BROWSER_CONNECTION.get("use_existing", False)

        # Rest of your code remains the same
        # Initialize browser controller
        print("Setting up virtual browser controller...")
        controller = VirtualBrowserController(page)

        # Create LangChain tools
        print("Creating tools...")
        tools = create_browser_tools(controller)

        # Create the agent with better error handling
        print("Creating agent with tools...")
        try:
            agent_executor = create_agent(tools, OPENAI_API_KEY)
            print("Agent created successfully!")
        except Exception as agent_error:
            print(f"\n❌ ERROR CREATING AGENT: {str(agent_error)}")
            print("\nDetailed traceback:")
            traceback.print_exc()
            print("\nTrying to continue without the agent...")
            return  # Exit the function if agent creation fails

        # Main interaction loop
        keep_running = True
        while keep_running:
            # Get user query
            user_query = input("\nEnter your instruction for the browser agent (or type 'exit' to quit): ")

            if user_query.lower() in ['exit', 'quit', 'q']:
                break

            # Execute task with proper input format
            print(f"\nExecuting: {user_query}\n")
            start_time = time.time()

            try:
                response = agent_executor.invoke({"input": user_query})
                end_time = time.time()

                # Print results
                print("\n" + "="*50)
                print(f"Execution completed in {end_time - start_time:.2f} seconds")
                print("="*50)
                print(response.get("output", "No output received"))
                print("="*50)

                # Ask if user wants to continue
                continue_input = input("\nContinue with another task? (y/n): ")
                if continue_input.lower() != 'y':
                    keep_running = False

            except Exception as e:
                print(f"\nError during execution: {str(e)}")
                print("The agent encountered an error but the browser will remain open.")

                # Ask if user wants to try again or exit
                retry_input = input("\nTry another task? (y/n): ")
                if retry_input.lower() != 'y':
                    keep_running = False

    finally:
        # Pass the connection state to close_browser
        if 'playwright' in locals() and 'browser' in locals():
            # Ask if user wants to close the browser
            if using_connected_browser:
                close_input = input("\nDisconnect from browser? (y/n): ")
            else:
                close_input = input("\nClose browser? (y/n): ")

            if close_input.lower() == 'y':
                # Cleanup with appropriate mode
                print("Cleaning up browser resources...")
                close_browser(playwright, browser, is_connected=using_connected_browser)
            else:
                print("Browser left open. You can close it manually.")

if __name__ == "__main__":
    main()

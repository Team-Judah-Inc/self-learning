import sys
import os
import json
import termios
import tty
import datetime
from data_gen import (
    load_data, save_data, read_balances, create_user,
    create_account, create_card, simulate_days,
    create_manual_transaction, create_transfer_transaction
)

# --- ANSI COLOR CONSTANTS ---
BLUE = "\033[38;5;33m"
GREEN = "\033[38;5;82m"
YELLOW = "\033[38;5;226m"
RED = "\033[38;5;196m"
CYAN = "\033[38;5;51m"
MAGENTA = "\033[38;5;207m"
ORANGE = "\033[38;5;208m"
BOLD = "\033[1m"
RESET = "\033[0m"

# --- INPUT HELPER ---

def get_single_key_input(prompt, allow_esc=True):
    """Reads a single key press without waiting for Enter (Unix/macOS)."""
    print(prompt, end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        char = sys.stdin.read(1)
        if allow_esc and char == "\x1b":
            print("")
            return "\x1b"
        print(char) # Echo the choice
        return char
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# --- MENU DISPLAYS ---

def show_main_menu(current_date):
    print(f"\n{BOLD}{BLUE}=============================================={RESET}")
    print(f"{BOLD}{BLUE}    BANKING WORLD SIMULATOR - DASHBOARD      {RESET}")
    print(f"{BOLD}{BLUE}=============================================={RESET}")
    print(f"{CYAN}Current Date:{RESET} {YELLOW}{current_date}{RESET}")
    print(f"\n{BOLD}Main Actions:{RESET}")
    print(f"  {BOLD}{GREEN}[1]{RESET} Initialize World (Wipe & Reset)")
    print(f"  {BOLD}{GREEN}[2]{RESET} Evolve Time (Advance Days)")
    print(f"  {BOLD}{GREEN}[3]{RESET} View Balances & Stats")
    print(f"  {BOLD}{GREEN}[4]{RESET} Manual Management (Users/Transactions)")
    print(f"  {BOLD}{RED}[ESC]{RESET} Exit System")
    print(f"{BOLD}{BLUE}----------------------------------------------{RESET}")

def show_management_menu():
    print(f"\n{BOLD}{MAGENTA}--- Resource Management ---{RESET}")
    print(f"  {BOLD}{CYAN}[1]{RESET} Create New User")
    print(f"  {BOLD}{CYAN}[2]{RESET} Create New Account")
    print(f"  {BOLD}{CYAN}[3]{RESET} Create Manual Transaction")
    print(f"  {BOLD}{CYAN}[4]{RESET} Perform Inter-Account Transfer")
    print(f"  {BOLD}{YELLOW}[B]{RESET} Back to Main Menu")

# --- MAIN APPLICATION LOOP ---

def run_app():
    data = load_data()
    
    while True:
        os.system('clear') # Keep the terminal clean
        show_main_menu(data['metadata']['current_date'])
        
        choice = get_single_key_input(f"{BOLD}Select your path: {RESET}")

        if choice == "\x1b": # ESC
            print(f"\n{ORANGE}Shutting down simulation... Goodbye!{RESET}")
            save_data(data)
            break

        # 1. INITIALIZE
        if choice == "1":
            print(f"\n{RED}{BOLD}⚠️ WARNING:{RESET} This will wipe all data.")
            confirm = get_single_key_input("Are you sure? [Y/N]: ").lower()
            if confirm == 'y':
                data['users'], data['accounts'], data['cards'], data['transactions'] = [], [], [], []
                data['metadata']['current_date'] = "2025-01-01"
                for _ in range(5):
                    u = create_user(data)
                    a = create_account(data, u['user_id'])
                    create_card(data, a['account_id'])
                simulate_days(data, 30)
                print(f"\n{GREEN}Success: World initialized with 5 users.{RESET}")
                input("\nPress Enter to continue...")

        # 2. EVOLVE
        elif choice == "2":
            days_str = input(f"\n{BOLD}Enter number of days to advance: {RESET}")
            try:
                days = int(days_str)
                simulate_days(data, days)
                input("\nSimulation complete. Press Enter to continue...")
            except ValueError:
                print(f"{RED}Invalid number.{RESET}")

        # 3. BALANCES
        elif choice == "3":
            print(f"\n{BOLD}{GREEN}--- CURRENT FINANCIAL SNAPSHOT ---{RESET}\n")
            read_balances(data)
            input("\nPress Enter to return to menu...")

        # 4. MANAGEMENT SUB-MENU
        elif choice == "4":
            while True:
                show_management_menu()
                sub_choice = get_single_key_input(f"{BOLD}Management Action: {RESET}").lower()
                
                if sub_choice == 'b':
                    break
                
                if sub_choice == "1": # Create User
                    u = create_user(data)
                    print(f"\n{GREEN}Created User: {u['user_id']} ({u['username']}){RESET}")
                
                elif sub_choice == "2": # Create Account
                    uid = input("\nEnter User ID (e.g., u_1): ")
                    create_account(data, uid)
                    print(f"{GREEN}Account created.{RESET}")

                elif sub_choice == "3": # Manual Txn
                    link_id = input("\nEnter Card or Account ID: ")
                    amount = float(input("Enter Amount (Negative for debit): "))
                    create_manual_transaction(data, link_id, {"amount": amount})
                
                elif sub_choice == "4": # Transfer
                    f_id = input("\nFrom Account: ")
                    t_id = input("To Account: ")
                    amt = float(input("Amount: "))
                    create_transfer_transaction(data, f_id, t_id, {"amount": amt})

                save_data(data) # Save after every management action
        
        save_data(data)

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print(f"\n{RED}Emergency Stop Detected. Saving state...{RESET}")
        sys.exit()
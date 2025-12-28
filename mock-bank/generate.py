import sys
import os
import termios
import tty
import datetime

# --- IMPORT V4.0 MODULES FROM PACKAGE ---
# We now import from the 'data_gen' folder
try:
    from data_gen import (
        BankingSimulation, 
        JsonRepository, 
        run_simulation_loop, 
        process_manual_transaction, 
        process_transfer,
        DATA_DIR
    )
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("Ensure you have a folder named 'data_gen' containing '__init__.py', 'simulation.py', etc.\n")
    sys.exit(1)

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

# --- DISPLAY HELPERS ---

def show_main_menu(current_date):
    print(f"\n{BOLD}{BLUE}=============================================={RESET}")
    print(f"{BOLD}{BLUE}    BANKING WORLD SIMULATOR (V4.0)           {RESET}")
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

def display_balances(bank: BankingSimulation):
    print(f"\n{BOLD}{GREEN}--- CURRENT FINANCIAL SNAPSHOT ---{RESET}")
    print(f"{'USER ID':<10} | {'NAME':<20} | {'ACCOUNT':<10} | {'BALANCE':>12}")
    print("-" * 60)
    for acc in bank.accounts:
        name = f"{acc.owner.first_name} {acc.owner.last_name}"
        print(f"{acc.user_id:<10} | {name:<20} | {acc.account_id:<10} | ${acc.balance:>11.2f}")
    print("-" * 60)

# --- MAIN APPLICATION LOOP ---

def run_app():
    # 1. Initialize the V4.0 Architecture
    repo = JsonRepository(DATA_DIR)
    bank = BankingSimulation(repo)
    
    # 2. Load Data
    try:
        bank.load_world()
    except Exception:
        # If files don't exist, we start with empty state which is handled by repo
        pass

    while True:
        os.system('clear') # Keep the terminal clean
        
        # Access date from bank metadata
        curr_date = bank.metadata.get('current_date', "Unknown")
        show_main_menu(curr_date)
        
        choice = get_single_key_input(f"{BOLD}Select your path: {RESET}")

        if choice == "\x1b": # ESC
            print(f"\n{ORANGE}Shutting down simulation... Goodbye!{RESET}")
            bank.save_world()
            break

        # 1. INITIALIZE (Wipe)
        if choice == "1":
            print(f"\n{RED}{BOLD}⚠️ WARNING:{RESET} This will wipe all data.")
            confirm = get_single_key_input("Are you sure? [Y/N]: ").lower()
            if confirm == 'y':
                # Reset In-Memory State
                bank.users, bank.accounts, bank.cards = [], [], []
                bank.account_txns, bank.card_txns = [], []
                bank.metadata['current_date'] = datetime.date.today().isoformat()
                
                # Reseed
                print(f"\n{YELLOW} seeding world...{RESET}")
                for _ in range(5):
                    u = bank.create_user()
                    a = bank.create_account(u.user_id)
                    bank.create_card(a.account_id)
                
                # Initial evolution
                run_simulation_loop(bank, 30)
                print(f"\n{GREEN}Success: World initialized with 5 users.{RESET}")
                input("\nPress Enter to continue...")

        # 2. EVOLVE
        elif choice == "2":
            days_str = input(f"\n{BOLD}Enter number of days to advance: {RESET}")
            try:
                days = int(days_str)
                run_simulation_loop(bank, days)
                input("\nSimulation complete. Press Enter to continue...")
            except ValueError:
                print(f"{RED}Invalid number.{RESET}")
                input("Press Enter...")

        # 3. BALANCES
        elif choice == "3":
            display_balances(bank)
            input("\nPress Enter to return to menu...")

        # 4. MANAGEMENT SUB-MENU
        elif choice == "4":
            while True:
                show_management_menu()
                sub_choice = get_single_key_input(f"{BOLD}Management Action: {RESET}").lower()
                
                if sub_choice == 'b':
                    break
                
                if sub_choice == "1": # Create User
                    u = bank.create_user()
                    print(f"\n{GREEN}Created User: {u.user_id} ({u.first_name}){RESET}")
                
                elif sub_choice == "2": # Create Account
                    uid = input("\nEnter User ID (e.g., u_1): ")
                    acc = bank.create_account(uid)
                    if acc: print(f"{GREEN}Account {acc.account_id} created.{RESET}")
                    else: print(f"{RED}User not found.{RESET}")

                elif sub_choice == "3": # Manual Txn
                    link_id = input("\nEnter Card or Account ID: ")
                    try:
                        amt_str = input("Enter Amount (Negative for debit): ")
                        amount = float(amt_str)
                        process_manual_transaction(bank, link_id, {"amount": amount})
                    except ValueError:
                        print(f"{RED}Invalid amount.{RESET}")
                
                elif sub_choice == "4": # Transfer
                    f_id = input("\nFrom Account: ")
                    t_id = input("To Account: ")
                    try:
                        amt_str = input("Amount: ")
                        amt = float(amt_str)
                        process_transfer(bank, f_id, t_id, {"amount": amt})
                    except ValueError:
                         print(f"{RED}Invalid amount.{RESET}")

                bank.save_world() # Save after management actions
        
        # Save state after every main loop iteration
        bank.save_world()

if __name__ == "__main__":
    try:
        run_app()
    except KeyboardInterrupt:
        print(f"\n{RED}Emergency Stop Detected. Saving state...{RESET}")
        sys.exit()
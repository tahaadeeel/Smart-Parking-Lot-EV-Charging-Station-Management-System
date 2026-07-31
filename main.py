import sys
from facility_manager import FacilityManager

def main():
    fm = FacilityManager()
    while True:
        print("\n--- Smart Parking System ---")
        print("1. Generate Report")
        print("2. Export Sessions to CSV")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            print(fm.generate_report())
        elif choice == '2':
            print(fm.export_sessions_csv())
        elif choice == '3':
            print("Shutting down cleanly.")
            sys.exit(0)
        else:
            print("Invalid choice. (Full features available via REST API)")

if __name__ == "__main__":
    main()
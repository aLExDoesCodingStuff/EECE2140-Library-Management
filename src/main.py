# main.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import date 

# add the src folder to search path (make imports not break)
base_directory = Path.cwd()
if base_directory not in sys.path:
    sys.path.append(base_directory)

from persistence import load_state, save_state
from models.library import Library
from models.user import User
from auth.role import Role
from auth.access_control import AccessControl


base_directory = Path.cwd()
if base_directory not in sys.path:
    sys.path.append(base_directory)
# This path relies on the script being run from the 'src' directory (base_directory)
dataset_filepath = base_directory.parent/"Sample Datasets"/"books_new.csv"

# Load state and assign to global variables
library, userbase = load_state(dataset_filepath) 
current_user = None
inventory_count = 0 # NEW: Global variable for inventory status
for user_id, user_obj in userbase.items():
    if not hasattr(user_obj, 'checkout_history'):
        user_obj.checkout_history = {}
        
# Initialize Tkinter root window
root = tk.Tk()
main_content_frame = ttk.Frame(root)
main_content_frame.pack(fill='both', expand=True)

# Setup RBAC Roles
member_role = Role("member",["checkout_item","return_item"])  
admin_role = Role("admin",["add_item","remove_item","process_checkout","get_days_overdue","get_overdue_copies","check_overdue","catalog_system","list_inv","load_state","save_state","set_date"])

# =========================
# Inventory Loading Logic 
# =========================
def check_and_load_inventory():
    """Checks the CSV path and attempts to load inventory, updating the global count."""
    global inventory_count
    
    if library.inventory:
        inventory_count = len(library.inventory)
        print(f"[INIT] Inventory already contains {inventory_count} books from load_state.")
        return
        
    print(f"[INIT] Calculated CSV Path: {dataset_filepath}")
    
    if not dataset_filepath.exists():
        print(f"[INIT] CRITICAL ERROR: CSV file NOT FOUND at: {dataset_filepath}")
        print("[INIT] Please ensure you are running the script from the correct directory or the path is correct.")
        inventory_count = 0
        return
    
    print("[INIT] Inventory is empty after loading state. Attempting to parse CSV...")
    # library.parse_CSV now returns the number of books added
    books_added = library.parse_CSV(dataset_filepath) 
    inventory_count = books_added
    
    if inventory_count > 0:
        print(f"[INIT] Successfully loaded {inventory_count} books from CSV.")
    else:
        print("[INIT] WARNING: Inventory remains empty. Check console for [ERROR] output from parse_CSV.")

check_and_load_inventory()

# =========================
# Utility Functions
# =========================

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def is_admin(user_obj):
    # We check for a distinct admin permission (EECE0001)
    return library.ac.has_permission(user_obj.username, "set_date")

def save_state_and_exit():
    #Saves the global library object and userbase and closes the GUI
    global library, userbase, root
    
    if save_state(library, userbase):
        root.destroy()
    else:
        messagebox.showerror("Exit Error", "Failed to save library state. See console for details.")


def update_user_base(name_entry, frame_to_clear):
    #Registers a new user and updates the UI
    global userbase, library
    
    user_name = name_entry.get().strip()
    
    if not user_name:
        messagebox.showerror("Error", "Please enter your name.")
        return

    library.user_id_counter += 1
    new_user_id = f"EECE{library.user_id_counter:04d}" 
    
    new_user_obj = User(user_name)
    userbase[new_user_id] = new_user_obj
    
    # Assign default role to the new user
    library.ac.assign_role(new_user_obj.username, [member_role])
    
    clear_frame(frame_to_clear)
    
    ttk.Label(frame_to_clear, text="Registration Successful!", font=('Arial', 14, 'bold')).pack(pady=10)
    ttk.Label(frame_to_clear, text=f"Hello {user_name}, your user ID is {new_user_id}.").pack(pady=5)
    ttk.Label(frame_to_clear, text="Please remember your ID for login.").pack(pady=5)
    
    ttk.Button(frame_to_clear, text="Return to Main Menu", command=show_main_menu).pack(pady=10)


def handle_login(login_entry):
    #Processes login attempt and transitions to the user menu on success
    global current_user, userbase
    user_id = login_entry.get().strip().upper()

    if user_id in userbase:
        current_user = userbase[user_id] 
        show_library_menu(current_user) # Redirects to admin menu if admin
    else:
        messagebox.showerror("Login Error", "Invalid User ID. Please try again or register.")
        login_entry.delete(0, tk.END)

# --- Admin Specific Handlers ---

def handle_set_date(date_entry, frame, user_obj):
    """Handles the system date change."""
    date_str = date_entry.get().strip()
    try:
        new_date = date.fromisoformat(date_str)
        
        # Call the library method (set_date handles permission check internally)
        library.set_date(new_date, user_obj)
        
        messagebox.showinfo("Date Updated", f"System date successfully set to {library.current_date}")
        
        # Refresh the admin menu to show the new date
        show_admin_menu(user_obj) 
        
    except ValueError:
        messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD (e.g., 2025-12-31).")
    except PermissionError as e:
        messagebox.showerror("Permission Denied", str(e))
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

        
def show_overdue_report(user_obj):
    #Displays a list of all overdue items in a new window
    
    try:
        # library.check_overdue handles permission check internally
        overdue_copies = library.check_overdue(user_obj)
        
        report_window = tk.Toplevel(root)
        report_window.title("Overdue Items Report")
        
        if not overdue_copies:
            ttk.Label(report_window, text="No items are currently overdue.").pack(padx=20, pady=20)
        else:
            report_text = tk.Text(report_window, height=15, width=60)
            report_text.pack(padx=20, pady=10)
            report_text.insert(tk.END, f"Overdue Items as of {library.current_date}:\n\n")
            
            # To get book name, we now have to search inventory for the copy
            for copy in overdue_copies:
                days_overdue = (library.current_date - copy['return_date']).days
                borrower = copy['borrowed_by'].username
                
                # Try to find the book name
                book_name = "Unknown Book"
                for book in library.inventory:
                    if copy in book.copies:
                        book_name = book.name
                        break
                        
                report_text.insert(tk.END, 
                                   f"Book: {book_name}\n"
                                   f"  - Borrower: {borrower}\n"
                                   f"  - Due Date: {copy['return_date']}\n"
                                   f"  - Days Overdue: {days_overdue}\n\n")

            report_text.config(state=tk.DISABLED)
            
        ttk.Button(report_window, text="Close", command=report_window.destroy).pack(pady=10)

    except PermissionError as e:
        messagebox.showerror("Permission Denied", str(e))
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred while generating report: {e}")


# --- Member Specific Handlers ---


def handle_checkout(book_obj, user_obj):
    #Handles the checkout attempt for a specific book object
    try:
        # Checkout item
        result_message = library.checkout_item(book_obj, user_obj)
        messagebox.showinfo("Checkout Action", result_message)
        show_library_menu(user_obj)
        
    except PermissionError as e:
        messagebox.showerror("Permission Denied", str(e))
    except Exception as e:
        # Handles waitlist message or system error
        messagebox.showerror("Checkout Failed/Waitlist", str(e))
        show_library_menu(user_obj) # Return to menu after Waitlist message

def handle_return(book_entry, user_obj, frame):
    #Handles the book return process from the list of checked-out items
    try:
        checked_out_books_unique = []
        # Get unique books the user has (to match the displayed list)
        for book, copy in user_obj.items_checked_out:
            # only show one entry per unique book name for simplicity in return selection
            if book not in [b for b, c in checked_out_books_unique]:
                 checked_out_books_unique.append((book, copy))
        
        book_index = int(book_entry.get().strip()) - 1
        
        if book_index < 0 or book_index >= len(checked_out_books_unique):
            messagebox.showerror("Error", "Invalid selection. Please enter a valid number from the list.")
            return

        # Get the actual book object
        book_to_return = checked_out_books_unique[book_index][0]

        # Call the return method
        result_message = library.return_item(book_to_return, user_obj)
        
        messagebox.showinfo("Return Successful", result_message)
        show_library_menu(user_obj)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for the book index.")
    except PermissionError as e:
        messagebox.showerror("Permission Denied", str(e))
    except Exception as e:
        messagebox.showerror("System Error", str(e))


def handle_search(search_term_entry, search_by_var, user_obj):
    #Processes search and displays results
    search_term = search_term_entry.get().strip()
    search_by = search_by_var.get()
    
    if not search_term:
        messagebox.showerror("Error", "Please enter a search term.")
        return

    # Check for empty inventory before searching
    if not library.inventory:
        messagebox.showerror("Error", "The library catalog is empty. Please check the console for CSV loading errors.")
        return
        
    # Call the new library search_catalog method
    results = library.search_catalog(search_term, search_by)
    
    show_search_results(user_obj, results, search_term, search_by)


# =========================
# UI Display Functions (MODIFIED FOR ADMIN/MEMBER)
# =========================

def show_admin_menu(user_obj):
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text=f"Admin Portal: {user_obj.username}", font=('Arial', 18, 'bold')).pack(pady=20)
    
    # System/Time Management
    ttk.Label(main_content_frame, text=f"Current Library Date: {library.current_date}").pack(pady=(5, 10))

    # Overdue Report Button
    ttk.Button(main_content_frame, text="View Overdue Items ⚠️", command=lambda: show_overdue_report(user_obj)).pack(pady=5, ipadx=20)
    
    # Set Date Functionality
    ttk.Label(main_content_frame, text="Set System Date (YYYY-MM-DD):").pack(pady=5)
    date_entry = ttk.Entry(main_content_frame, width=15)
    date_entry.insert(0, str(date.today())) # Pre-fill with today's date
    date_entry.pack(pady=5)
    ttk.Button(main_content_frame, text="Change Date", command=lambda: handle_set_date(date_entry, main_content_frame, user_obj)).pack(pady=10, ipadx=10)
    
    ttk.Separator(main_content_frame, orient='horizontal').pack(fill='x', pady=10)
    
    # User Actions (Now using search/return UI)
    ttk.Button(main_content_frame, text="Search for a Book", command=lambda: show_search_form(user_obj)).pack(pady=5, ipadx=10)
    ttk.Button(main_content_frame, text="Return a Book", command=lambda: book_return(user_obj)).pack(pady=5, ipadx=10)
    
    ttk.Button(main_content_frame, text="Logout", command=show_main_menu).pack(pady=20)


def show_library_menu(user_obj):
    
    #Shows the appropriate menu (Admin or Member) based on user permissions.
    if is_admin(user_obj):
        show_admin_menu(user_obj)
        return
        
    # Standard Member Menu
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text=f"Welcome, {user_obj.username}!", font=('Arial', 16, 'bold')).pack(pady=20)
    
    if user_obj.items_checked_out:
        ttk.Label(main_content_frame, text=f"Checked out: {len(user_obj.items_checked_out)} item(s)").pack()

    # Search and Recommendation buttons
    ttk.Button(main_content_frame, text="Search for a Book", command=lambda: show_search_form(user_obj)).pack(pady=10, ipadx=10)
    ttk.Button(main_content_frame, text="Get Book Recommendations", command=lambda: show_recommendations(user_obj)).pack(pady=10, ipadx=10)
    ttk.Button(main_content_frame, text="Return a Book", command=lambda: book_return(user_obj)).pack(pady=10, ipadx=10)
    
    ttk.Button(main_content_frame, text="Logout", command=show_main_menu).pack(pady=20)


def show_new_user_form():
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text="New User Registration", font=('Arial', 16)).pack(pady=15)
    ttk.Label(main_content_frame, text="What is your name?").pack(pady=5)
    new_user_name_entry = ttk.Entry(main_content_frame, width=30)
    new_user_name_entry.pack(pady=5)
    ttk.Button(
        main_content_frame, 
        text="Register and Get ID",
        command=lambda: update_user_base(new_user_name_entry, main_content_frame)
    ).pack(pady=10)
    ttk.Button(main_content_frame, text="Back", command=show_main_menu).pack(pady=5)

def show_login_form():
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text="User Login", font=('Arial', 16)).pack(pady=15)
    ttk.Label(main_content_frame, text="Enter your EECE ID:").pack(pady=5)
    login_entry = ttk.Entry(main_content_frame, width=30)
    login_entry.pack(pady=5)
    ttk.Button(main_content_frame, text="Log In", command=lambda: handle_login(login_entry)).pack(pady=10)
    ttk.Button(main_content_frame, text="Back", command=show_main_menu).pack(pady=5)

def book_selection(user_obj):
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text="Available Books", font=('Arial', 16, 'bold')).pack(pady=10)
    
    ttk.Label(main_content_frame, text="Please use the Search feature to find and checkout a book.", foreground='blue').pack(pady=10)
    ttk.Button(main_content_frame, text="Go to Search", command=lambda: show_search_form(user_obj)).pack(pady=10)

    # Return to appropriate menu
    if is_admin(user_obj):
        ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=20)
    else:
        ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=20)


def book_return(user_obj):
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text="Your Checked Out Books", font=('Arial', 16, 'bold')).pack(pady=10)

    # show a list of unique books checked out by the user
    checked_out_books_unique = []
    
    if not user_obj.items_checked_out:
        ttk.Label(main_content_frame, text="You have no books checked out.").pack(pady=10)
        # Return to appropriate menu
        if is_admin(user_obj):
            ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=20)
        else:
            ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=20)
        return
        
    inventory_text = tk.Text(main_content_frame, height=5, width=50)
    
    # Store the unique book objects and list them in the text widget
    listable_books = [] 
    
    for book, copy in user_obj.items_checked_out:
        if book not in [b for b, c in checked_out_books_unique]:
            checked_out_books_unique.append((book, copy))
            listable_books.append(book)
            # IMPORTANT: The number shown here is for *this* list, not the main inventory list
            inventory_text.insert(tk.END, f"{len(listable_books)}. {book.name} | Due: {copy['return_date']}\n")


    inventory_text.config(state=tk.DISABLED)
    inventory_text.pack(pady=5, padx=10)
    
    ttk.Label(main_content_frame, text="Enter the **number** of the book to return (from the list above):").pack(pady=5)
    book_entry = ttk.Entry(main_content_frame, width=10)
    book_entry.pack(pady=5)
    
    ttk.Button(main_content_frame, text = 'Return', command = lambda: handle_return(book_entry, user_obj, main_content_frame)).pack(pady=10)
    
    # Return to appropriate menu
    if is_admin(user_obj):
        ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=5)
    else:
        ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=5)


# --- UI Functions ---

def show_search_form(user_obj):
    #Displays the form for searching the catalo."""
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text="Find a Book", font=('Arial', 16, 'bold')).pack(pady=15)
    
    search_by_var = tk.StringVar(value='title') 

    # Search Type Selection 
    search_frame = ttk.Frame(main_content_frame)
    search_frame.pack(pady=10)
    ttk.Label(search_frame, text="Search By:").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(search_frame, text="Title", variable=search_by_var, value='title').pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(search_frame, text="Author", variable=search_by_var, value='author').pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(search_frame, text="Genre", variable=search_by_var, value='genre').pack(side=tk.LEFT, padx=5)
    
    # Search Term Entry
    ttk.Label(main_content_frame, text="Search Term:").pack(pady=5)
    search_term_entry = ttk.Entry(main_content_frame, width=40)
    search_term_entry.pack(pady=5)
    
    # Search Button
    ttk.Button(
        main_content_frame, 
        text="Search Catalog",
        command=lambda: handle_search(search_term_entry, search_by_var, user_obj)
    ).pack(pady=10)

    # Back Button
    if is_admin(user_obj):
        ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=20)
    else:
        ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=20)


def show_search_results(user_obj, results, search_term, search_by):
    #Displays the results of a book search
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text=f"Search Results for '{search_term}' ({search_by})", font=('Arial', 16, 'bold')).pack(pady=10)
    
    if not results:
        ttk.Label(main_content_frame, text="No books found matching your search.", foreground='red').pack(pady=10)
    else:
        # Display results in a scrollable list
        results_frame = ttk.Frame(main_content_frame)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Using a Treeview for a cleaner list display
        tree = ttk.Treeview(results_frame, columns=("Title", "Author", "Genre"), show="headings", height=10)
        tree.heading("Title", text="Title")
        tree.heading("Author", text="Author")
        tree.heading("Genre", text="Genre")
        tree.column("Title", width=200)
        tree.column("Author", width=150)
        tree.column("Genre", width=100)
        
        # Store book objects with their treeview ID for easy retrieval
        book_id_map = {}
        for i, book in enumerate(results):
            # Check availability (simple check for at least one copy being available)
            is_available = any(copy['borrowed_by'] is None for copy in book.copies)
            availability_text = "🟢 Available" if is_available else "🟡 Waitlist"
            
            item_id = tree.insert("", tk.END, values=(book.name, book.author, book.genre), 
                                  tags=('available' if is_available else 'waitlist',))
            
            # Map the treeview item ID to the actual Book object
            book_id_map[item_id] = book

            # Update the title column to include availability
            tree.set(item_id, 'Title', f"{book.name} ({availability_text})")


        tree.pack(fill='both', expand=True)

        def checkout_selected(event):
            """Handles the checkout command when a book is selected in the Treeview."""
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showerror("Error", "Please select a book from the list.")
                return
            
            selected_book = book_id_map.get(selected_item)
            if selected_book:
                handle_checkout(selected_book, user_obj)

        tree.bind('<Double-1>', checkout_selected) # Double click to checkout

        # Instruction Label
        ttk.Label(main_content_frame, text="Double-click a book to Check Out or Join Waitlist.", font=('Arial', 10)).pack(pady=5)
    
    # Back to Search Button
    ttk.Button(main_content_frame, text="New Search", command=lambda: show_search_form(user_obj)).pack(pady=10)
    
    # Back to Menu Button
    if is_admin(user_obj):
        ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=5)
    else:
        ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=5)


def show_recommendations(user_obj):
    #Displays a list of recommended books based on checkout history
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text="Recommended Books", font=('Arial', 16, 'bold')).pack(pady=10)

    # Get recommendations
    recommendations = library.recommend_books(user_obj)
        
    if not recommendations:
        ttk.Label(main_content_frame, text="No new recommendations available right now. Checkout a book to start receiving recommendations!", foreground='red', wraplength=400).pack(pady=10)
    else:
        
        # Display recommendations (using a Treeview for consistency)
        results_frame = ttk.Frame(main_content_frame)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        tree = ttk.Treeview(results_frame, columns=("Title", "Author", "Genre"), show="headings", height=5)
        tree.heading("Title", text="Title")
        tree.heading("Author", text="Author")
        tree.heading("Genre", text="Genre")
        tree.column("Title", width=200)
        tree.column("Author", width=150)
        tree.column("Genre", width=100)

        book_id_map = {}
        for i, book in enumerate(recommendations):
            is_available = any(copy['borrowed_by'] is None for copy in book.copies)
            availability_text = "🟢 Available" if is_available else "🟡 Waitlist"
            
            item_id = tree.insert("", tk.END, values=(book.name, book.author, book.genre))
            book_id_map[item_id] = book
            tree.set(item_id, 'Title', f"{book.name} ({availability_text})")

        tree.pack(fill='both', expand=True)

        def checkout_selected(event):
            """Handles the checkout command when a book is selected in the Treeview."""
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showerror("Error", "Please select a book from the list.")
                return
            
            selected_book = book_id_map.get(selected_item)
            if selected_book:
                handle_checkout(selected_book, user_obj)

        tree.bind('<Double-1>', checkout_selected) # Double click to checkout

        # Instruction Label
        ttk.Label(main_content_frame, text="Double-click a recommendation to Check Out or Join Waitlist.", font=('Arial', 10)).pack(pady=5)
    
    # Back to Menu Button
    if is_admin(user_obj):
        ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=20)
    else:
        ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=20)


def show_main_menu():
    #Displays the initial welcome screen and user choice buttons
    clear_frame(main_content_frame)
    global current_user, inventory_count
    current_user = None 
    
    ttk.Label(main_content_frame, text="Welcome to Group 12's Library System!", font=('Arial', 16, 'bold')).pack(pady=(20, 5))
    ttk.Label(main_content_frame, text="Please choose an option to continue.").pack(pady=(0, 20))

    # Inventory status display
    if inventory_count > 0:
        status_text = f"Catalog Status: {inventory_count} books loaded successfully. 🟢"
        status_color = 'green'
    else:
        status_text = "Catalog Status: Inventory is empty. 🔴 Check console for file path errors."
        status_color = 'red'
        
    ttk.Label(main_content_frame, text=status_text, foreground=status_color).pack(pady=(0, 20))
    
    ttk.Button(
        main_content_frame,
        text="New User Registration",
        command=show_new_user_form
    ).pack(
        ipadx=10, ipady=10, pady=5
    )
    
    ttk.Button(
        main_content_frame,
        text="Existing User Login",
        command=show_login_form
    ).pack(
        ipadx=10, ipady=10, pady=5
    )
        
    ttk.Button(
        main_content_frame,
        text="Exit (Save State)",
        command=save_state_and_exit 
    ).pack(
        ipadx=10, ipady=10, pady=5
    )

# =========================
# MAIN PROGRAM EXECUTION
# =========================

root.title('Library System')
root.geometry('550x550') 
root.resizable(True, True)

# Initialize a default admin user if the userbase is empty
if not userbase:
    admin = User("admin")
    library.ac.assign_role(admin.username, [admin_role,member_role])
    library.user_id_counter += 1
    admin_id = f"EECE{library.user_id_counter:04d}"
    userbase[admin_id] = admin 
    print(f"[SETUP] Default admin created with ID: {admin_id}")

show_main_menu()
root.mainloop()

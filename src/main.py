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
dataset_filepath = base_directory.parent/"Sample Datasets"/"books_new.csv"

# Load state and assign to global variables
library, userbase = load_state(dataset_filepath) 
current_user = None

# Initialize Tkinter root window
root = tk.Tk()
main_content_frame = ttk.Frame(root)
main_content_frame.pack(fill='both', expand=True)

# Setup RBAC Roles
member_role = Role("member",["checkout_item","return_item"])  
admin_role = Role("admin",["add_item","remove_item","process_checkout","get_days_overdue","get_overdue_copies","check_overdue","catalog_system","list_inv","load_state","save_state","set_date"])

# =========================
# Utility Functions
# =========================

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def is_admin(user_obj):
    # We check for a distinct admin permission like 'set_date' or check username == 'admin'
    return library.ac.has_permission(user_obj.username, "set_date")

def save_state_and_exit():
    """Saves the global library object and userbase and closes the GUI."""
    global library, userbase, root
    
    if save_state(library, userbase):
        root.destroy()
    else:
        messagebox.showerror("Exit Error", "Failed to save library state. See console for details.")


def update_user_base(name_entry, frame_to_clear):
    """Registers a new user and updates the UI."""
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
    """Processes login attempt and transitions to the user menu on success."""
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
    """Displays a list of all overdue items in a new window."""
    
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

def handle_checkout(book_entry, user_obj, frame):
    try:
        book_index = int(book_entry.get().strip()) - 1
        if book_index < 0 or book_index >= len(library.inventory):
            messagebox.showerror("Error", "Invalid book index. Please enter a valid number from the list.")
            return

        book_to_checkout = library.inventory[book_index]
        library.checkout_item(book_to_checkout, user_obj)
        messagebox.showinfo(
            "Checkout Successful",  # Title for the pop-up
            'Your checkout was successful!' # The successful message 
        )
        show_library_menu(user_obj)
        
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for the book index.")
    except PermissionError as e:
        messagebox.showerror("Permission Denied", str(e))
    except Exception as e:
        # Check for specific library-side errors (e.g., no available copy, already checked out, etc.)
        messagebox.showerror("System Error", f"An error occurred: {e}")

def handle_return(book_entry, user_obj, frame):
    try:
        book_index = int(book_entry.get().strip()) - 1
        if book_index < 0 or book_index >= len(library.inventory):
            messagebox.showerror("Error", "Invalid book index. Please enter a valid number from the list.")
            return

        book_to_return = library.inventory[book_index]
        library.return_item(book_to_return, user_obj)
        clear_frame(frame)
        messagebox.showinfo(
            "Return Successful",  # Title for the pop-up
            'Your return was successful!' # The successful message
        )
        show_library_menu(user_obj)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for the book index.")
    except PermissionError as e:
        messagebox.showerror("Permission Denied", str(e))
    except Exception as e:
        messagebox.showerror("System Error", f"An error occurred: {e}")


# =========================
# UI Display Functions (MODIFIED FOR ADMIN/MEMBER)
# =========================

def show_admin_menu(user_obj):
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text=f"Admin Portal: {user_obj.username}", font=('Arial', 18, 'bold')).pack(pady=20)
    
    # 1. System/Time Management
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
    
    # Basic Library Actions (Still available to admin)
    ttk.Button(main_content_frame, text="Checkout Book (Member Actions)", command=lambda: book_selection(user_obj)).pack(pady=5, ipadx=10)
    ttk.Button(main_content_frame, text="Return Book (Member Actions)", command=lambda: book_return(user_obj)).pack(pady=5, ipadx=10)
    
    ttk.Button(main_content_frame, text="Logout", command=show_main_menu).pack(pady=20)


def show_library_menu(user_obj):
    """
    Shows the appropriate menu (Admin or Member) based on user permissions.
    """
    if is_admin(user_obj):
        show_admin_menu(user_obj)
        return
        
    # Standard Member Menu
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text=f"Welcome, {user_obj.username}!", font=('Arial', 16, 'bold')).pack(pady=20)
    
    if user_obj.items_checked_out:
        ttk.Label(main_content_frame, text=f"Checked out: {len(user_obj.items_checked_out)} item(s)").pack()

    ttk.Button(main_content_frame, text="Checkout a Book", command=lambda: book_selection(user_obj)).pack(pady=10, ipadx=10)
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
    
    inventory_text = tk.Text(main_content_frame, height=10, width=50)
    for i, book in enumerate(library.inventory, start=1):
        inventory_text.insert(tk.END, f"{i}. {book}\n")
    inventory_text.config(state=tk.DISABLED) 
    inventory_text.pack(pady=5, padx=10)

    ttk.Label(main_content_frame, text="Enter the **number** of the book to checkout:").pack(pady=5)
    book_entry = ttk.Entry(main_content_frame, width=10)
    book_entry.pack(pady=5)
    
    ttk.Button(main_content_frame, text = 'Checkout', command = lambda: handle_checkout(book_entry, user_obj, main_content_frame)).pack(pady=10)
    
    # Return to appropriate menu
    if is_admin(user_obj):
        ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=5)
    else:
        ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=5)


def book_return(user_obj):
    clear_frame(main_content_frame)
    ttk.Label(main_content_frame, text="Your Checked Out Books", font=('Arial', 16, 'bold')).pack(pady=10)

    if not user_obj.items_checked_out:
        ttk.Label(main_content_frame, text="You have no books checked out.").pack(pady=10)
        if is_admin(user_obj):
            ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=20)
        else:
            ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=20)
        return
        
    inventory_text = tk.Text(main_content_frame, height=5, width=50)
    for i, (book, copy) in enumerate(user_obj.items_checked_out):
        try:
            main_index = library.inventory.index(book) + 1
            inventory_text.insert(tk.END, f"{main_index}. {book.name} | Due: {copy['return_date']}\n")
        except ValueError:
            inventory_text.insert(tk.END, f"- {book.name} | Due: {copy['return_date']} (Unknown Index)\n")

    inventory_text.config(state=tk.DISABLED)
    inventory_text.pack(pady=5, padx=10)
    
    ttk.Label(main_content_frame, text="Enter the **number** of the book from the main list to return:").pack(pady=5)
    book_entry = ttk.Entry(main_content_frame, width=10)
    book_entry.pack(pady=5)
    
    ttk.Button(main_content_frame, text = 'Return', command = lambda: handle_return(book_entry, user_obj, main_content_frame)).pack(pady=10)
    
    # Return to appropriate menu
    if is_admin(user_obj):
        ttk.Button(main_content_frame, text="Back to Admin Menu", command=lambda: show_admin_menu(user_obj)).pack(pady=5)
    else:
        ttk.Button(main_content_frame, text="Back to Menu", command=lambda: show_library_menu(user_obj)).pack(pady=5)


def show_main_menu():
    """Displays the initial welcome screen and user choice buttons."""
    clear_frame(main_content_frame)
    global current_user
    current_user = None 
    
    ttk.Label(main_content_frame, text="Welcome to Group 12's Library System!", font=('Arial', 16, 'bold')).pack(pady=(20, 5))
    ttk.Label(main_content_frame, text="Please choose an option to continue.").pack(pady=(0, 20))
    
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

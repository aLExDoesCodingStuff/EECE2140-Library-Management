# Library Management Program

A comprehensive system for managing a library's inventory, programmed in Python as a final project for EECE2140.

**Team Members:**
- Alex Messier
- Brooke Wassmann
- Harshitha Vemula


## Quick Start
- To begin the program, simply run main.py (stored in the src folder of our project directory). This will launch the GUI.
- Create a user account, and login using your automatically-generated user ID. This will take you to the home page of the interface, where you can access the features of the library catalog system. 
- To view an authorized admin account, enter the user ID: **EECE0001**. From here, you can view some summarized information about the library, such as a list of overdue items. You also have the ability to change the system date for testing purposes. 
## Key  Features
- Allows registered library users to checkout and return books, place books on hold, or search the library database
- Assigns a designated expiration window to checked-out books and tracks overdue books
- Manages waitlists which automatically notify users as copies of books are returned and become available
- Library inventory can be searched by book title, author, or genre
- Saves Library state (registered users,outstanding loans, waitlists, pending holds) between sessions in a .pkl file, and rebuilds at runtime
- Role-based access control system to limit destructive changes (ie, adding/removing Books from inventory) to authorized users with admin status
- GUI allows users to easily search the library database, make checkout/return/hold requests, receive book recommendations based on their previous checkout history
## Possible Future Features
- Incorporate expanded admin features directly into admin page of GUI
- Add data visualization


		




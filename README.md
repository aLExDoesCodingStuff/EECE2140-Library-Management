# Library Management Program

A comprehensive system for managing a library's inventory, programmed in Python as a final project for EECE2140.

**Team Members:**
- Alex Messier
- Brooke Wassmann
- Harshitha Vemula

## Key  Features
- Allows registered library users to checkout and return books, place books on hold, or search the library database
- Assigns a designated expiration window to checked-out books and tracks overdue books
- Manages waitlists which automatically notify users as copies of books are returned and become available
- Library inventory can be searched by book title, author, or genre
- Saves Library state (book checkouts, waitlist positions, pending holds) between sessions in a CSV file, to be restored at next runtime.

## Planned Features
- Role-based access control system to limit destructive changes (ie, adding/removing Books from inventory) to authorized users with admin status
- GUI to allow users to easily make checkout/hold requests, receive relevant notifications (eg, changes to waitlist status, or notices about overdue items), and search the library database

		




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
- Emailing system
- Increase inventory
- Implement overdue book system via fees and bars

## Video Demos
- For a user experience demo, view the link below
- https://teams.microsoft.com/l/meetingrecap?driveId=b%21UesGN8rnq0irz1vV2rVCDhuScXfm7s9Lj1DjCTXKZ5CDg39gyIitRp44iFx-p5St&driveItemId=01Y5MZMPSGLNZNBPUBKJELLW25IWOJHKLL&sitePath=https%3A%2F%2Fnortheastern-my.sharepoint.com%2F%3Av%3A%2Fg%2Fpersonal%2Fwassmann_b_northeastern_edu%2FEUZbctC-gVJItdtdRZyTqWsBw0IrEcGXMI9pWoF9CCkzCw&fileUrl=https%3A%2F%2Fnortheastern-my.sharepoint.com%2Fpersonal%2Fwassmann_b_northeastern_edu%2FDocuments%2FRecordings%2FMeeting%2520with%2520Brooke%2520Wassmann-20251205_192945-Meeting%2520Recording.mp4%3Fweb%3D1&threadId=19%3Ameeting_NWIwZmM5NjUtODNjOC00NDA4LThmODMtZWM3ZTY5ODA0ZmU3%40thread.v2&organizerId=f43b5d6d-186d-4135-b39e-cfb230a1b768&tenantId=a8eec281-aaa3-4dae-ac9b-9a398b9215e7&callId=eeac44c7-c1df-4df6-82ad-75828e3eccdd&threadType=Meeting&meetingType=MeetNow&subType=RecapSharingLink_RecapCore

- For a admin experience demo, view the link below this
- https://teams.microsoft.com/l/meetingrecap?driveId=b%21UesGN8rnq0irz1vV2rVCDhuScXfm7s9Lj1DjCTXKZ5CDg39gyIitRp44iFx-p5St&driveItemId=01Y5MZMPSBHWPWM4FF3BDJFOMHMID63CDO&sitePath=https%3A%2F%2Fnortheastern-my.sharepoint.com%2F%3Av%3A%2Fg%2Fpersonal%2Fwassmann_b_northeastern_edu%2FEUE9n2ZwpdhGkrmHYgftiG4BKmOYK71jO5TGSXC6HacIrw&fileUrl=https%3A%2F%2Fnortheastern-my.sharepoint.com%2Fpersonal%2Fwassmann_b_northeastern_edu%2FDocuments%2FRecordings%2FMeeting%2520with%2520Brooke%2520Wassmann-20251205_193130-Meeting%2520Recording.mp4%3Fweb%3D1&threadId=19%3Ameeting_NWIwZmM5NjUtODNjOC00NDA4LThmODMtZWM3ZTY5ODA0ZmU3%40thread.v2&organizerId=f43b5d6d-186d-4135-b39e-cfb230a1b768&tenantId=a8eec281-aaa3-4dae-ac9b-9a398b9215e7&callId=eeac44c7-c1df-4df6-82ad-75828e3eccdd&threadType=Meeting&meetingType=MeetNow&subType=RecapSharingLink_RecapCore

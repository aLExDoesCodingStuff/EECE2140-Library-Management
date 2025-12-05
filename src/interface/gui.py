import tkinter as tk
from tkinter import ttk
import sys

from models.library import Library
from auth.access_control import AccessControl


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # -------------------------
        # Window Configuration
        # -------------------------
        self.title("Library Portal")
        self.geometry("400x450")
        self.resizable(False, False)

        # This dictionary stores all our frames
        self.frames = {}

        # Instantiate and store frames
        for F in (HomeFrame, SearchFrame):
            frame = F(self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the home frame to start
        self.show_frame(HomeFrame)

    def show_frame(self, frame_class):
        """Bring a frame to the front (like navigating pages)."""
        frame = self.frames[frame_class]
        frame.tkraise()


# ============================================================
#                      HOME FRAME
# ============================================================

class HomeFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)

        # Title
        title = ttk.Label(
            self,
            text="Library User Portal",
            font=("TkDefaultFont", 16, "bold")
        )
        title.pack(pady=(0, 10))

        # Divider
        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(0, 20))

        # Buttons Container
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="both", expand=True)

        # Buttons arranged vertically
        search_btn = ttk.Button(
            btn_frame,
            text="Search Inventory",
            command=lambda: master.show_frame(SearchFrame)
        )
        search_btn.pack(fill="x", pady=5)

        return_btn = ttk.Button(
            btn_frame,
            text="Return Item",
            command=lambda: print("Return Item")
        )
        return_btn.pack(fill="x", pady=5)

        profile_btn = ttk.Button(
            btn_frame,
            text="View Profile",
            command=lambda: print("View Profile")
        )
        profile_btn.pack(fill="x", pady=5)


# ============================================================
#                       SEARCH FRAME
# ============================================================

class SearchFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)

        # VARIABLES
        self.search_terms = tk.StringVar()
        self.search_mode = tk.StringVar(value="by author")

        # -------------------------
        # TOP AREA (2x2 GRID)
        # -------------------------
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x")

        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        # First row
        ttk.Label(top_frame, text="Search:").grid(row=0, column=0, sticky="w", padx=5, pady=5)

        options = ["by author", "by title", "by genre"]
        self.option_menu = ttk.OptionMenu(
            top_frame,
            self.search_mode,
            self.search_mode.get(),
            *options
        )
        self.option_menu.grid(row=0, column=1, sticky="e", padx=5, pady=5)

        # Second row
        entry = ttk.Entry(top_frame, textvariable=self.search_terms)
        entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        search_button = ttk.Button(top_frame, text="Search", command=self.perform_search)
        search_button.grid(row=1, column=1, sticky="e", padx=5, pady=5)

        # -------------------------
        # SCROLLABLE RESULTS AREA
        # -------------------------

        # Create container with border
        border_frame = ttk.Frame(self, borderwidth=2, relief="groove")
        border_frame.pack(fill="both", expand=True, pady=10)

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(border_frame)
        scrollbar = ttk.Scrollbar(border_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Internal frame inside canvas
        self.results_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")

        # Ensure scrolling region updates
        self.results_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # -------------------------
        # BACK BUTTON
        # -------------------------
        ttk.Button(self, text="Back", command=lambda: master.show_frame(HomeFrame)).pack(pady=5)

    # ----------------------------------------------------
    #             SEARCH BUTTON ACTION
    # ----------------------------------------------------
    def perform_search(self):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        text = self.search_terms.get()
        mode = self.search_mode.get()

        # Fake results for demonstration
        fake_results = [
            f"Result {i+1}: '{text}' ({mode})"
            for i in range(25)
        ]

        for i, result in enumerate(fake_results):
            label = ttk.Label(self.results_frame, text=result)
            label.grid(row=i, column=0, sticky="w", pady=2)


# ============================================================
# RUN THE APPLICATION
# ============================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()

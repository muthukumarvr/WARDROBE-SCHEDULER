import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
from PIL import Image, ImageTk, ImageDraw, ImageFont
import colorsys
import math
import datetime
import os
import requests
import numpy as np
from datetime import datetime, date, timedelta
from calendar import monthrange
from tkcalendar import Calendar
import datetime
import csv
import random
from wardrobe_app_gui_main import CalendarView

class CalendarView(tk.Toplevel):
    def __init__(self, parent, cursor, conn):
        super().__init__(parent)
        self.title("Wardrobe Calendar")
        self.geometry("1200x800")
        self.cursor = cursor
        self.conn = conn
        self.configure(bg="#f5f7fa")
        
        # Current date tracking
        self.current_date = date.today()
        self.selected_date = None  # Track selected date for details
        
        # Main container
        main_frame = tk.Frame(self, bg="#f5f7fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with navigation
        self.create_header(main_frame)
        
        # Calendar display
        self.calendar_frame = tk.Frame(main_frame, bg="#f5f7fa")
        self.calendar_frame.pack(fill=tk.BOTH, expand=True)
        
        # Outfit details panel
        self.details_frame = tk.Frame(main_frame, bg="#f5f7fa", height=300)
        self.details_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Create the calendar
        self.create_calendar()
        
        # Load schedule data
        self.load_schedule_data()
        
        # Fill calendar with data
        self.fill_calendar_data()
        
    def create_header(self, parent):
        """Create header with navigation controls"""
        header_frame = tk.Frame(parent, bg="#f5f7fa")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Month navigation
        nav_frame = tk.Frame(header_frame, bg="#f5f7fa")
        nav_frame.pack(side=tk.LEFT)
        
        # Previous month button
        prev_btn = tk.Button(nav_frame, text="◀", command=self.prev_month,
                            font=("Arial", 14), bg="#4361ee", fg="white", bd=0)
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        # Month/year display
        self.month_year_label = tk.Label(
            nav_frame, text="", 
            font=("Segoe UI", 18, "bold"), 
            bg="#f5f7fa", fg="#2b2d42"
        )
        self.month_year_label.pack(side=tk.LEFT, padx=10)
        
        # Next month button
        next_btn = tk.Button(nav_frame, text="▶", command=self.next_month,
                           font=("Arial", 14), bg="#4361ee", fg="white", bd=0)
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Today button
        today_btn = tk.Button(header_frame, text="Today", command=self.show_today,
                             font=("Segoe UI", 10), bg="#f72585", fg="white", bd=0)
        today_btn.pack(side=tk.LEFT, padx=10)
        
    def create_calendar(self):
        """Create the calendar grid"""
        # Clear previous grid
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
            
        # Day names header
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        days_frame = tk.Frame(self.calendar_frame, bg="#f5f7fa")
        days_frame.pack(fill=tk.X)
        
        for i, day in enumerate(day_names):
            tk.Label(
                days_frame, text=day, width=15, height=2,
                font=("Segoe UI", 10, "bold"), 
                bg="#f5f7fa", fg="#2b2d42"
            ).grid(row=0, column=i, padx=2, pady=2)
        
        # Calendar grid with cards
        grid_frame = tk.Frame(self.calendar_frame, bg="#f5f7fa")
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create 6 rows x 7 columns grid of day cards
        self.day_cards = []
        for row in range(6):
            row_cards = []
            for col in range(7):
                card = tk.Frame(
                    grid_frame, 
                    bg="white",
                    bd=1, relief=tk.RAISED,
                    width=150, height=100
                )
                card.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
                card.grid_propagate(False)
                
                # Day number label
                day_label = tk.Label(
                    card, text="", font=("Segoe UI", 10, "bold"),
                    bg="white", fg="#2b2d42"
                )
                day_label.place(x=5, y=5)
                
                # Outfit indicator
                outfit_indicator = tk.Label(
                    card, text="", font=("Segoe UI", 8),
                    bg="white", fg="#8d99ae"
                )
                outfit_indicator.place(x=5, y=30)
                
                # Mini outfit preview
                preview_frame = tk.Frame(card, bg="white")
                preview_frame.place(x=5, y=50, width=140, height=40)
                
                row_cards.append({
                    'frame': card,
                    'day_label': day_label,
                    'outfit_indicator': outfit_indicator,
                    'preview_frame': preview_frame
                })
                
                # Bind click event
                card.bind("<Button-1>", lambda e, r=row, c=col: self.show_day_details(r, c))
            
            self.day_cards.append(row_cards)
        
        # Configure grid weights
        for i in range(6):
            grid_frame.rowconfigure(i, weight=1)
        for i in range(7):
            grid_frame.columnconfigure(i, weight=1)
    
    def load_schedule_data(self):
        """Load schedule data for the current month"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Get first and last day of month
        first_day, num_days = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)
        
        # Query for specific date schedules
        self.cursor.execute(
            "SELECT day, shirt, pant, shoes FROM schedule "
            "WHERE day BETWEEN ? AND ?",
            (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        specific_schedules = self.cursor.fetchall()
        
        # Query for weekly schedules
        self.cursor.execute(
            "SELECT day, shirt, pant, shoes FROM schedule "
            "WHERE day IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')")
        weekly_schedules = self.cursor.fetchall()
        
        # Combine schedules (specific dates override weekly)
        self.schedule_data = {}
        
        # Add weekly schedules first
        for day_name, shirt, pant, shoes in weekly_schedules:
            # Store by day name for later lookup
            self.schedule_data[day_name] = (shirt, pant, shoes)
        
        # Add specific date schedules (override weekly)
        for date_str, shirt, pant, shoes in specific_schedules:
            # Store by date string
            self.schedule_data[date_str] = (shirt, pant, shoes)
    
    def fill_calendar_data(self):
        """Update calendar display for current month"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Update month/year label
        self.month_year_label.config(text=self.current_date.strftime("%B %Y"))
        
        # Get first day of month and number of days
        first_day, num_days = monthrange(year, month)
        
        # Calculate days from previous month to show
        prev_month_days = (first_day + 1) % 7  # +1 to convert to 0=Sunday
        
        # Fill in calendar days
        day_num = 1
        for row in range(6):
            for col in range(7):
                card = self.day_cards[row][col]

                if (row == 0 and col < prev_month_days) or day_num > num_days:
                    # Previous or next month day
                    card['day_label'].config(text="")
                    card['outfit_indicator'].config(text="")
                    card['frame'].config(bg="#f0f0f0")
                else:
                    # Current month day
                    current_date = date(year, month, day_num)
                    card['day_label'].config(text=str(day_num))
                    
                    # Highlight today
                    if current_date == date.today():
                        card['frame'].config(bg="#e3f2fd")
                        card['day_label'].config(fg="white")
                    else:
                        card['frame'].config(bg="white")
                        card['day_label'].config(fg="#2b2d42")
                    
                    # Clear previous preview
                    for widget in card['preview_frame'].winfo_children():
                        widget.destroy()
                    
                    # Check for specific date outfit
                    date_str = current_date.strftime("%Y-%m-%d")
                    outfit = self.schedule_data.get(date_str)
                    
                    if not outfit:
                        # Check for weekly schedule
                        day_name = current_date.strftime("%A")
                        outfit = self.schedule_data.get(day_name)
                    
                    if outfit:
                        shirt, pant, shoes = outfit
                        items = [x for x in [shirt, pant, shoes] if x]
                        card['outfit_indicator'].config(text=f"{len(items)} items")
                        
                        # Create mini outfit preview
                        self.create_mini_preview(card['preview_frame'], shirt, pant, shoes)
                    
                    day_num += 1

    def create_mini_preview(self, parent, top, bottom, shoes):
        """Create mini outfit preview for calendar view"""
        if not top and not bottom and not shoes:
            return
            
        # Create a canvas for visual representation
        preview_canvas = tk.Canvas(parent, bg=parent['bg'], highlightthickness=0, 
                                 width=140, height=40)
        preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw simple outfit representation
        if top:
            preview_canvas.create_rectangle(20, 5, 50, 20, fill="#4cc9f0", outline="")
            preview_canvas.create_text(35, 12, text="T", font=("Arial", 8), fill="white")
        
        if bottom:
            preview_canvas.create_rectangle(20, 25, 50, 40, fill="#4895ef", outline="")
            preview_canvas.create_text(35, 32, text="B", font=("Arial", 8), fill="white")
        
        if shoes:
            preview_canvas.create_rectangle(60, 30, 80, 40, fill="#560bad", outline="")
            preview_canvas.create_rectangle(90, 30, 110, 40, fill="#560bad", outline="")
            preview_canvas.create_text(70, 35, text="S", font=("Arial", 8), fill="white")
            preview_canvas.create_text(100, 35, text="S", font=("Arial", 8), fill="white")
    
    def show_day_details(self, row, col):
        """Show outfit details for selected day"""
        # Clear previous details
        for widget in self.details_frame.winfo_children():
            widget.destroy()
            
        # Get the day card
        card = self.day_cards[row][col]
        day_num = card['day_label']['text']
        
        if not day_num:
            return
        
        # Get the actual date
        year = self.current_date.year
        month = self.current_date.month
        self.selected_date = date(year, month, int(day_num))
        
        # Create details panel
        details_panel = tk.Frame(
            self.details_frame, 
            bg="white",
            bd=1, relief=tk.RAISED,
            padx=15, pady=15
        )
        details_panel.pack(fill=tk.BOTH, expand=True)
        
        # Selected date label
        date_label = tk.Label(
            details_panel, text=self.selected_date.strftime("%A, %B %d, %Y"), 
            font=("Segoe UI", 14, "bold"), 
            bg="white", fg="#2b2d42"
        )
        date_label.pack(anchor="w", pady=(0, 10))
        
        # Get outfit for this day
        date_str = self.selected_date.strftime("%Y-%m-%d")
        outfit = self.schedule_data.get(date_str)
        
        if not outfit:
            # Check for weekly schedule
            day_name = self.selected_date.strftime("%A")
            outfit = self.schedule_data.get(day_name)
        
        if outfit:
            shirt, pant, shoes = outfit
            self.show_outfit_details(details_panel, shirt, pant, shoes)
        else:
            tk.Label(
                details_panel, text="No outfit scheduled for this day", 
                font=("Segoe UI", 12), 
                bg="white", fg="#8d99ae"
            ).pack(pady=20)
    
    def show_outfit_details(self, parent, shirt, pant, shoes):
        """Show detailed outfit information"""
        # Outfit items container
        items_frame = tk.Frame(parent, bg="white")
        items_frame.pack(fill=tk.X, pady=10)
        
        # Column headers
        headers = ["Item Type", "Item Name", "Color", "Fabric"]
        for col, header in enumerate(headers):
            tk.Label(
                items_frame, text=header, 
                font=("Segoe UI", 10, "bold"), 
                bg="white", fg="#2b2d42"
            ).grid(row=0, column=col, padx=10, pady=5, sticky="w")
        
        # Display each outfit item
        row = 1
        for item_type, item_name in [("Top", shirt), ("Bottom", pant), ("Shoes", shoes)]:
            if not item_name:
                continue
                
            # Get item details from database
            self.cursor.execute(
                "SELECT color, fabric FROM items WHERE name=?",
                (item_name,)
            )
            item_data = self.cursor.fetchone()
            
            if item_data:
                color, fabric = item_data
            else:
                color, fabric = "N/A", "N/A"
            
            # Create row for this item
            tk.Label(
                items_frame, text=item_type, 
                font=("Segoe UI", 10), 
                bg="white", fg="#2b2d42"
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            tk.Label(
                items_frame, text=item_name, 
                font=("Segoe UI", 10), 
                bg="white", fg="#2b2d42"
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            tk.Label(
                items_frame, text=color, 
                font=("Segoe UI", 10), 
                bg="white", fg="#2b2d42"
            ).grid(row=row, column=2, padx=10, pady=5, sticky="w")
            
            tk.Label(
                items_frame, text=fabric, 
                font=("Segoe UI", 10), 
                bg="white", fg="#2b2d42"
            ).grid(row=row, column=3, padx=10, pady=5, sticky="w")
            
            row += 1
            
        # Add rating display if outfit is complete
        if shirt and pant and shoes:
            rating_frame = tk.Frame(parent, bg="white")
            rating_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                rating_frame, text="Outfit Rating:", 
                font=("Segoe UI", 11, "bold"), 
                bg="white", fg="#2b2d42"
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            # Get rating from database
            self.cursor.execute(
                "SELECT rating FROM outfit_ratings WHERE shirt=? AND pant=? AND shoes=?",
                (shirt, pant, shoes))
            rating_row = self.cursor.fetchone()
            rating = rating_row[0] if rating_row else "Not rated"
            
            if isinstance(rating, int):
                stars = "★" * rating + "☆" * (5 - rating)
                tk.Label(
                    rating_frame, text=stars, 
                    font=("Segoe UI", 14), 
                    bg="white", fg="#FFD700"
                ).pack(side=tk.LEFT)
            else:
                tk.Label(
                    rating_frame, text=rating, 
                    font=("Segoe UI", 11), 
                    bg="white", fg="#8d99ae"
                ).pack(side=tk.LEFT)
    
    def prev_month(self):
        """Move to previous month"""
        first_day = self.current_date.replace(day=1)
        self.current_date = first_day - timedelta(days=1)
        self.load_schedule_data()
        self.fill_calendar_data()

    def next_month(self):
        """Move to next month"""
        days_in_month = monthrange(self.current_date.year, self.current_date.month)[1]
        last_day = self.current_date.replace(day=days_in_month)
        self.current_date = last_day + timedelta(days=1)
        self.load_schedule_data()
        self.fill_calendar_data()

    def show_today(self):
        """Show current month and today's date"""
        self.current_date = date.today()
        self.load_schedule_data()
        self.fill_calendar_data()

class GradientButton(tk.Canvas):
    def __init__(self, master, text, command, color1, color2, width=120, height=40, corner_radius=10, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, **kwargs)
        self.command = command
        self.color1 = color1
        self.color2 = color2
        self.corner_radius = corner_radius
        self.text = text
        self.width = width
        self.height = height
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self.draw_button()
    
    def draw_button(self):
        self.delete("all")
        # Create gradient
        for i in range(self.height):
            ratio = i / self.height
            r = int(self.hex_to_rgb(self.color1)[0] * (1 - ratio) + self.hex_to_rgb(self.color2)[0] * ratio)
            g = int(self.hex_to_rgb(self.color1)[1] * (1 - ratio) + self.hex_to_rgb(self.color2)[1] * ratio)
            b = int(self.hex_to_rgb(self.color1)[2] * (1 - ratio) + self.hex_to_rgb(self.color2)[2] * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.create_line(0, i, self.width, i, fill=color)
        
        # Add text
        self.create_text(self.width/2, self.height/2, text=self.text, fill="white", font=("Segoe UI", 10, "bold"))
    
    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _on_click(self, event):
        self.command()
    
    def _on_enter(self, event):
        self.config(cursor="hand2")
        # Lighten the button on hover
        self.color1 = self.lighten_color(self.color1, 0.1)
        self.color2 = self.lighten_color(self.color2, 0.1)
        self.draw_button()
    
    def _on_leave(self, event):
        self.config(cursor="")
        # Restore original colors
        self.color1 = self.darken_color(self.color1, 0.1)
        self.color2 = self.darken_color(self.color2, 0.1)
        self.draw_button()
    
    def lighten_color(self, hex_color, factor):
        r, g, b = self.hex_to_rgb(hex_color)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def darken_color(self, hex_color, factor):
        r, g, b = self.hex_to_rgb(hex_color)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f'#{r:02x}{g:02x}{b:02x}'

class EnhancedScheduleView(tk.Toplevel):
    def __init__(self, parent, cursor, conn):
        super().__init__(parent)
        self.title("✨ Wardrobe Schedule Pro")
        self.geometry("1400x800")
        self.cursor = cursor
        self.conn = conn
        self.configure(bg="#f5f7fa")
        
        # Modern styling
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f5f7fa")
        self.style.configure("TLabel", background="#f5f7fa", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=6)
        
        # Animation variables
        self.current_week = date.today()
        self.animation_running = False
        
        # Create main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with navigation
        self.create_header(main_frame)
        
        # Schedule display
        self.schedule_frame = ttk.Frame(main_frame)
        self.schedule_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create day columns
        self.day_frames = []
        self.create_week_view()
        
        # Load initial data
        self.load_week_schedule()
        
        # Add hover effects
        self.setup_hover_effects()
        
        # Add keyboard shortcuts
        self.bind("<Left>", lambda e: self.prev_week())
        self.bind("<Right>", lambda e: self.next_week())
        self.bind("<Up>", lambda e: self.show_today())
    
    def create_header(self, parent):
        """Create animated header with navigation"""
        header_frame = ttk.Frame(parent, style="TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Week navigation
        nav_frame = ttk.Frame(header_frame, style="TFrame")
        nav_frame.pack(side=tk.LEFT)
        
        # Previous week button with icon
        prev_btn = GradientButton(
            nav_frame, text="◀", command=self.prev_week,
            color1="#4361ee", color2="#3a0ca3",
            width=50, height=50, corner_radius=25
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        # Week label with smooth transition
        self.week_label = tk.Label(
            nav_frame, text="", 
            font=("Segoe UI", 18, "bold"), 
            bg="#f5f7fa", fg="#2b2d42"
        )
        self.week_label.pack(side=tk.LEFT, padx=10)
        
        # Next week button with icon
        next_btn = GradientButton(
            nav_frame, text="▶", command=self.next_week,
            color1="#4361ee", color2="#3a0ca3",
            width=50, height=50, corner_radius=25
        )
        next_btn.pack(side=tk.LEFT, padx=5)
        
        # Today button with pulse animation
        today_btn = GradientButton(
            header_frame, text="Today", command=self.show_today,
            color1="#f72585", color2="#b5179e",
            width=120, height=50, corner_radius=25
        )
        today_btn.pack(side=tk.LEFT, padx=10)
        
        # Add quick action buttons
        action_frame = ttk.Frame(header_frame, style="TFrame")
        action_frame.pack(side=tk.RIGHT)
        
        # Print button
        print_btn = GradientButton(
            action_frame, text="🖨️ Print", command=self.print_schedule,
            color1="#4cc9f0", color2="#4895ef",
            width=120, height=40, corner_radius=20
        )
        print_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        export_btn = GradientButton(
            action_frame, text="📤 Export", command=self.export_schedule,
            color1="#06d6a0", color2="#118ab2",
            width=120, height=40, corner_radius=20
        )
        export_btn.pack(side=tk.LEFT, padx=5)

    def create_stats_panel(self, parent):
        stats_frame = tk.Frame(parent, bg=self.colors['card'], bd=1, relief=tk.RAISED, padx=15, pady=15)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            stats_frame, text="Monthly Stats", 
            font=("Segoe UI", 14, "bold"), 
            bg=self.colors['card'], fg=self.colors['text']
        ).pack(anchor="w", pady=(0, 10))
        
        # Stats grid
        stats_grid = tk.Frame(stats_frame, bg=self.colors['card'])
        stats_grid.pack(fill=tk.X)
        
        # Stats items
        stats = [
            ("Scheduled Days", "25/30", "#4cc9f0"),
            ("Worn Items", "42", "#4895ef"),
            ("Favorite Outfit", "Blue Shirt+Jeans", "#560bad"),
            ("Avg. Rating", "4.2 ★", "#f72585")
        ]
        
        for i, (title, value, color) in enumerate(stats):
            stat_frame = tk.Frame(stats_grid, bg=self.colors['card'])
            stat_frame.grid(row=0, column=i, padx=10, sticky="nsew")
            
            tk.Label(
                stat_frame, text=title, 
                font=("Segoe UI", 10), 
                bg=self.colors['card'], fg=self.colors['light_text']
            ).pack(anchor="w")
            
            tk.Label(
                stat_frame, text=value, 
                font=("Segoe UI", 12, "bold"), 
                bg=self.colors['card'], fg=color
            ).pack(anchor="w")

    def create_calendar_grid(self):
        # Clear previous grid
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
            
        if self.current_view == "month":
            self.create_month_view()
        else:
            self.create_week_view()

    def create_month_view(self):
        # Day names header
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        days_frame = tk.Frame(self.calendar_frame, bg=self.colors['background'])
        days_frame.pack(fill=tk.X)
        
        for i, day in enumerate(day_names):
            tk.Label(
                days_frame, text=day, width=15, height=2,
                font=("Segoe UI", 10, "bold"), 
                bg=self.colors['background'], fg=self.colors['text']
            ).grid(row=0, column=i, padx=2, pady=2)
        
        # Calendar grid with cards
        grid_frame = tk.Frame(self.calendar_frame, bg=self.colors['background'])
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create 6 rows x 7 columns grid of day cards
        self.day_cards = []
        for row in range(6):
            row_cards = []
            for col in range(7):
                card = tk.Frame(
                    grid_frame, 
                    bg=self.colors['card'],
                    bd=1, relief=tk.RAISED,
                    width=150, height=100
                )
                card.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
                card.grid_propagate(False)
                
                # Day number label
                day_label = tk.Label(
                    card, text="", font=("Segoe UI", 10, "bold"),
                    bg=self.colors['card'], fg=self.colors['text']
                )
                day_label.place(x=5, y=5)
                
                # Outfit indicator
                outfit_indicator = tk.Label(
                    card, text="", font=("Segoe UI", 8),
                    bg=self.colors['card'], fg=self.colors['light_text']
                )
                outfit_indicator.place(x=5, y=30)
                
                # Mini outfit preview
                preview_frame = tk.Frame(card, bg=self.colors['card'])
                preview_frame.place(x=5, y=50, width=140, height=40)
                
                row_cards.append({
                    'frame': card,
                    'day_label': day_label,
                    'outfit_indicator': outfit_indicator,
                    'preview_frame': preview_frame
                })
                
                # Bind click event
                card.bind("<Button-1>", lambda e, r=row, c=col: self.show_day_details(r, c))
            
            self.day_cards.append(row_cards)
        
        # Configure grid weights
        for i in range(6):
            grid_frame.rowconfigure(i, weight=1)
        for i in range(7):
            grid_frame.columnconfigure(i, weight=1)
            
        # Fill with data
        self.fill_month_data()
    
    def create_week_view(self):
        """Create calendar-style week view with animations"""
        # Clear previous view
        for widget in self.schedule_frame.winfo_children():
            widget.destroy()
        
        # Header with day names and dates
        header_frame = ttk.Frame(self.schedule_frame, style="TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Calculate week dates
        start_date = self.current_week - timedelta(days=self.current_week.weekday())
        self.week_dates = [start_date + timedelta(days=i) for i in range(7)]
        
        # Create day headers
        for i, day_date in enumerate(self.week_dates):
            day_header = ttk.Frame(header_frame, style="TFrame")
            day_header.grid(row=0, column=i, padx=2, pady=2, sticky="nsew")
            
            # Day name
            day_name = day_date.strftime("%A")
            tk.Label(
                day_header, text=day_name[:3], 
                font=("Segoe UI", 12, "bold"), 
                bg="#f5f7fa", fg="#2b2d42"
            ).pack()
            
            # Date
            date_str = day_date.strftime("%d %b")
            date_label = tk.Label(
                day_header, text=date_str, 
                font=("Segoe UI", 14, "bold"), 
                bg="#f5f7fa", fg="#2b2d42"
            )
            date_label.pack()
            
            # Highlight today
            if day_date == date.today():
                day_header.config(style="Accent.TFrame")
                for child in day_header.winfo_children():
                    child.config(bg="#f72585", fg="white")
            
            # Configure grid weights
            header_frame.columnconfigure(i, weight=1)
        
        # Main content area
        content_frame = ttk.Frame(self.schedule_frame, style="TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create day columns
        self.day_frames = []
        for i in range(7):
            day_frame = ttk.Frame(
                content_frame, 
                style="Card.TFrame",
                relief=tk.RAISED, 
                borderwidth=1
            )
            day_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            # Outfit content with scrollbar
            canvas = tk.Canvas(day_frame, bg="white", highlightthickness=0)
            scrollbar = ttk.Scrollbar(day_frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas, style="TFrame")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.day_frames.append({
                'frame': day_frame,
                'canvas': canvas,
                'scrollable_frame': scrollable_frame,
                'date': self.week_dates[i]
            })
            
            # Configure grid weights
            content_frame.columnconfigure(i, weight=1)
    
    def fill_month_data(self):
        """Update calendar display for current month"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Update month/year label
        self.month_year_label.config(text=self.current_date.strftime("%B %Y"))
        
        # Get first day of month and number of days
        first_day, num_days = monthrange(year, month)
        
        # Calculate days from previous month to show
        prev_month_days = (first_day + 1) % 7  # +1 to convert to 0=Sunday
        
        # Fill in calendar days
        day_num = 1
        for row in range(6):
            for col in range(7):
                card = self.day_cards[row][col]

                if day_num <= num_days:
                    # Current month day
                    current_date = date(year, month, day_num)
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    # Check for outfit in schedule data
                    outfit = self.schedule_data.get(date_str)
                    
                    if outfit:
                        shirt, pant, shoes = outfit
                        items = [x for x in [shirt, pant, shoes] if x]
                        card['outfit_indicator'].config(text=f"{len(items)} items")
                        
                        # Store outfit data for redrawing
                        card['outfit_data'] = (shirt, pant, shoes)
                        
                        # Create mini outfit preview
                        preview_frame = card['preview_frame']
                        preview_canvas = tk.Canvas(preview_frame, bg=preview_frame['bg'], 
                                                highlightthickness=0, width=130, height=40)
                        preview_canvas.pack(fill=tk.BOTH, expand=True)
                        card['preview_canvas'] = preview_canvas
                        self.draw_mini_preview(card)
                        
                    day_num += 1

                
                if (row == 0 and col < prev_month_days) or day_num > num_days:
                    # Previous or next month day
                    card['day_label'].config(text="")
                    card['outfit_indicator'].config(text="")
                    card['frame'].config(bg="#f0f0f0")
                else:
                    # Current month day
                    current_date = date(year, month, day_num)
                    card['day_label'].config(text=str(day_num))
                    
                    # Highlight today
                    if current_date == date.today():
                        card['frame'].config(bg=self.colors['today'])
                        card['day_label'].config(fg="white")
                    else:
                        card['frame'].config(bg=self.colors['card'])
                        card['day_label'].config(fg=self.colors['text'])
                    
                    # Clear previous preview
                    for widget in card['preview_frame'].winfo_children():
                        widget.destroy()
                    
                    # Check for outfit
                    self.cursor.execute(
                        "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
                        (current_date.strftime("%Y-%m-%d"),))
                    outfit = self.cursor.fetchone()
                    
                    if outfit and any(outfit):
                        shirt, pant, shoes = outfit
                        items = [x for x in [shirt, pant, shoes] if x]
                        card['outfit_indicator'].config(text=f"{len(items)} items")
                        
                        # Create mini outfit preview
                        self.create_mini_preview(card['preview_frame'], shirt, pant, shoes)
                    
                    day_num += 1

    def fill_week_data(self):
        """Update week view display"""
        start_date = self.current_date - timedelta(days=self.current_date.weekday())
        self.month_year_label.config(
            text=f"{start_date.strftime('%b %d')} - {(start_date + timedelta(days=6)).strftime('%b %d, %Y')}"
        )
        
        for card in self.week_cards:

             # Get outfit for this day from schedule data
            date_str = card['date'].strftime("%Y-%m-%d")
            outfit = self.schedule_data.get(date_str)
            
            if outfit:
                shirt, pant, shoes = outfit
                # Store outfit data for redrawing
                card['outfit_data'] = (shirt, pant, shoes)
                self.create_week_outfit_preview(card['outfit_frame'], shirt, pant, shoes)

            # Clear previous content
            for widget in card['outfit_frame'].winfo_children():
                widget.destroy()
                
            # Highlight today
            if card['date'] == date.today():
                card['frame'].config(bg=self.colors['today'])
            else:
                card['frame'].config(bg=self.colors['card'])
            
            # Get outfit for this day
            self.cursor.execute(
                "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
                (card['date'].strftime("%Y-%m-%d"),))
            outfit = self.cursor.fetchone()
            
            if outfit:
                shirt, pant, shoes = outfit
                self.create_week_outfit_preview(card['outfit_frame'], shirt, pant, shoes)
            else:
                tk.Label(
                    card['outfit_frame'], text="No outfit scheduled", 
                    font=("Segoe UI", 10), 
                    bg=self.colors['card'], fg=self.colors['light_text']
                ).pack(pady=20)

    def create_mini_preview(self, parent, top, bottom, shoes):
        """Create mini outfit preview for month view"""
        # Create a canvas for visual representation
        preview_canvas = tk.Canvas(parent, bg=parent['bg'], highlightthickness=0, 
                                 width=140, height=40)
        preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw simple outfit representation
        if top:
            preview_canvas.create_rectangle(20, 5, 50, 20, fill="#4cc9f0", outline="")
            preview_canvas.create_text(35, 12, text="T", font=("Arial", 8), fill="white")
        
        if bottom:
            preview_canvas.create_rectangle(20, 25, 50, 40, fill="#4895ef", outline="")
            preview_canvas.create_text(35, 32, text="B", font=("Arial", 8), fill="white")
        
        if shoes:
            preview_canvas.create_rectangle(60, 30, 80, 40, fill="#560bad", outline="")
            preview_canvas.create_rectangle(90, 30, 110, 40, fill="#560bad", outline="")
            preview_canvas.create_text(70, 35, text="S", font=("Arial", 8), fill="white")
            preview_canvas.create_text(100, 35, text="S", font=("Arial", 8), fill="white")
    

    def create_week_outfit_preview(self, parent, top, bottom, shoes):
        """Create outfit preview for week view"""
        tk.Label(
            parent, text="Outfit for Today", 
            font=("Segoe UI", 11, "bold"), 
            bg=parent['bg'], fg=self.colors['text']
        ).pack(anchor="w", pady=(0, 10))
        
        items_frame = tk.Frame(parent, bg=parent['bg'])
        items_frame.pack(fill=tk.X, pady=5)
        
        if top:
            self.create_outfit_item(items_frame, "Top:", "icons/shirt.png", top)
        if bottom:
            self.create_outfit_item(items_frame, "Bottom:", "icons/pants.png", bottom)
        if shoes:
            self.create_outfit_item(items_frame, "Shoes:", "icons/shoes.png", shoes)
            
        # Add rating display
        rating_frame = tk.Frame(parent, bg=parent['bg'])
        rating_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            rating_frame, text="Rating:", 
            font=("Segoe UI", 10), 
            bg=parent['bg'], fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        # Get rating
        self.cursor.execute(
            "SELECT rating FROM outfit_ratings WHERE shirt=? AND pant=? AND shoes=?",
            (top, bottom, shoes))
        rating_row = self.cursor.fetchone()
        rating = rating_row[0] if rating_row else 0
        
        stars = ""
        for i in range(5):
            stars += "★" if i < rating else "☆"
        
        tk.Label(
            rating_frame, text=stars, 
            font=("Segoe UI", 14), 
            bg=parent['bg'], fg="#FFD700"
        ).pack(side=tk.LEFT, padx=5)

    def create_outfit_item(self, parent, label, icon_path, item_name):
        """Create an outfit item display with icon"""
        frame = tk.Frame(parent, bg=parent['bg'])
        frame.pack(fill=tk.X, pady=3)
        
        # Icon
        try:
            icon_img = Image.open(icon_path)
            icon_img = icon_img.resize((20, 20), Image.LANCZOS)
            icon = ImageTk.PhotoImage(icon_img)
            icon_label = tk.Label(frame, image=icon, bg=parent['bg'])
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=(0, 5))
        except:
            # Use text icon if image not found
            tk.Label(frame, text="●", font=("Segoe UI", 12), 
                    bg=parent['bg'], fg=self.colors['text']).pack(side=tk.LEFT, padx=(0, 5))
        
        # Label
        tk.Label(
            frame, text=label, 
            font=("Segoe UI", 11), 
            bg=parent['bg'], fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        # Item name
        item_label = tk.Label(
            frame, text=self.truncate_text(item_name, 20), 
            font=("Segoe UI", 11), 
            bg=parent['bg'], fg=self.colors['text']
        )
        item_label.pack(side=tk.LEFT, padx=5)

    def create_details_panel(self, parent):
        details_frame = tk.Frame(
            parent, 
            bg=self.colors['card'],
            bd=1, relief=tk.RAISED,
            padx=15, pady=15
        )
        details_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Selected date label
        self.selected_date_label = tk.Label(
            details_frame, text="Select a date to view outfit", 
            font=("Segoe UI", 14, "bold"), 
            bg=self.colors['card'], fg=self.colors['text']
        )
        self.selected_date_label.pack(anchor="w")
        
        # Outfit details container
        outfit_container = tk.Frame(details_frame, bg=self.colors['card'])
        outfit_container.pack(fill=tk.X, pady=10)
        
        # Outfit items with icons
        self.outfit_items = {
            'top': self.create_outfit_item(outfit_container, "Top:", "icons/shirt.png"),
            'bottom': self.create_outfit_item(outfit_container, "Bottom:", "icons/pants.png"),
            'shoes': self.create_outfit_item(outfit_container, "Shoes:", "icons/shoes.png")
        }
        
        # Action buttons
        btn_frame = tk.Frame(details_frame, bg=self.colors['card'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.update_btn = GradientButton(
            btn_frame, text="Update Outfit", command=self.update_outfit,
            color1=self.colors['primary'], color2=self.colors['secondary'],
            width=150, height=40, corner_radius=20
        )
        self.update_btn.pack(side=tk.LEFT, padx=5)
        self.update_btn.config(state=tk.DISABLED)
        
        self.mark_worn_btn = GradientButton(
            btn_frame, text="Mark as Worn", command=self.mark_as_worn,
            color1="#4cc9f0", color2="#4895ef",
            width=150, height=40, corner_radius=20
        )
        self.mark_worn_btn.pack(side=tk.LEFT, padx=5)
        self.mark_worn_btn.config(state=tk.DISABLED)
        
        # Outfit Rating Section
        rating_frame = tk.Frame(details_frame, bg=self.colors['card'])
        rating_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            rating_frame, text="Outfit Rating:", 
            font=("Segoe UI", 12), 
            bg=self.colors['card'], fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        self.rating_stars = []
        stars_frame = tk.Frame(rating_frame, bg=self.colors['card'])
        stars_frame.pack(side=tk.LEFT, padx=5)
        
        for i in range(5):
            star = tk.Label(
                stars_frame, text="★", font=("Segoe UI", 16),
                fg="#cccccc", bg=self.colors['card'],
                cursor="hand2"
            )
            star.pack(side=tk.LEFT)
            star.bind("<Button-1>", lambda e, idx=i: self.set_rating(idx+1))
            self.rating_stars.append(star)
        
        self.save_rating_btn = GradientButton(
            rating_frame, text="Save Rating", command=self.save_outfit_rating,
            color1="#f72585", color2="#b5179e",
            width=120, height=35, corner_radius=15
        )
        self.save_rating_btn.pack(side=tk.LEFT, padx=10)
        self.save_rating_btn.config(state=tk.DISABLED)
        
        # Add outfit suggestions button
        suggest_btn = GradientButton(
            details_frame, text="Get Suggestions", command=self.get_outfit_suggestions,
            color1="#06d6a0", color2="#118ab2",
            width=150, height=35, corner_radius=15
        )
        suggest_btn.pack(side=tk.RIGHT, pady=5)

    def toggle_view(self):
        """Toggle between month and week view"""
        self.current_view = "week" if self.current_view == "month" else "month"
        self.create_calendar_grid()

    def prev_period(self):
        """Move to previous period based on current view"""
        if self.current_view == "month":
            first_day = self.current_date.replace(day=1)
            self.current_date = first_day - timedelta(days=1)
        else:
            self.current_date -= timedelta(days=7)
        self.update_calendar()

    def next_period(self):
        """Move to next period based on current view"""
        if self.current_view == "month":
            days_in_month = monthrange(self.current_date.year, self.current_date.month)[1]
            last_day = self.current_date.replace(day=days_in_month)
            self.current_date = last_day + timedelta(days=1)
        else:
            self.current_date += timedelta(days=7)
        self.update_calendar()

    def show_day_details_date(self, selected_date):
        """Show details for selected day (date version)"""
        self.selected_date = selected_date
        self.show_day_details_common()

    def show_day_details(self, row, col):
        """Show details for selected day (grid version)"""
        day_num = self.day_cards[row][col]['day_label']['text']
        if not day_num:
            return
        
        self.selected_date = date(
            self.current_date.year,
            self.current_date.month,
            int(day_num))
        self.show_day_details_common()

    def show_day_details_common(self):
        """Common functionality for showing day details"""
         # Get outfit for this day
        date_str = self.selected_date.strftime("%Y-%m-%d")
        
        # First check specific date schedule
        self.cursor.execute(
            "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
            (date_str,))
        outfit = self.cursor.fetchone()
        
        # Then check weekly schedule if no specific date
        if not outfit:
            day_of_week = self.selected_date.strftime("%A")
            self.cursor.execute(
                "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
                (day_of_week,))
            outfit = self.cursor.fetchone()
        
        if outfit:
            shirt, pant, shoes = outfit
            self.outfit_items['top'].config(text=shirt if shirt else "None")
            self.outfit_items['bottom'].config(text=pant if pant else "None")
            self.outfit_items['shoes'].config(text=shoes if shoes else "None")
        else:
            self.outfit_items['top'].config(text="None")
            self.outfit_items['bottom'].config(text="None")
            self.outfit_items['shoes'].config(text="None")
        # Update selected date label
        self.selected_date_label.config(
            text=self.selected_date.strftime("%A, %B %d, %Y")
        )
        
        # Enable buttons
        self.update_btn.config(state=tk.NORMAL)
        self.mark_worn_btn.config(state=tk.NORMAL)
        self.save_rating_btn.config(state=tk.NORMAL)
        
        # Get outfit for this day
        self.cursor.execute(
            "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
            (self.selected_date.strftime("%Y-%m-%d"),))
        outfit = self.cursor.fetchone()
        
        if outfit:
            shirt, pant, shoes = outfit
            self.outfit_items['top'].config(text=shirt if shirt else "None")
            self.outfit_items['bottom'].config(text=pant if pant else "None")
            self.outfit_items['shoes'].config(text=shoes if shoes else "None")
        else:
            self.outfit_items['top'].config(text="None")
            self.outfit_items['bottom'].config(text="None")
            self.outfit_items['shoes'].config(text="None")
        
        # Get and display outfit rating
        self.display_outfit_rating(outfit)


    def display_outfit_rating(self, outfit):
        """Display rating for the current outfit"""
        # Reset all stars
        for star in self.rating_stars:
            star.config(fg="#cccccc")
        
        if outfit and all(outfit):
            shirt, pant, shoes = outfit
            self.cursor.execute(
                "SELECT rating FROM outfit_ratings WHERE shirt=? AND pant=? AND shoes=?",
                (shirt, pant, shoes))
            rating_row = self.cursor.fetchone()
            
            if rating_row:
                rating = rating_row[0]
                for i in range(rating):
                    self.rating_stars[i].config(fg="#FFD700")  # Gold color for active stars

    def set_rating(self, stars):
        """Set rating visually"""
        for i in range(5):
            if i < stars:
                self.rating_stars[i].config(fg="#FFD700")
            else:
                self.rating_stars[i].config(fg="#cccccc")
        
        self.current_rating = stars

    def save_outfit_rating(self):
        """Save the outfit rating to database"""
        if not self.selected_date or not hasattr(self, 'current_rating'):
            return
        
        shirt = self.outfit_items['top']['text']
        pant = self.outfit_items['bottom']['text']
        shoes = self.outfit_items['shoes']['text']
        
        if shirt == "None" or pant == "None" or shoes == "None":
            messagebox.showwarning("Warning", "Complete outfit required for rating")
            return
        
        # Create outfit_ratings table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS outfit_ratings (
                id INTEGER PRIMARY KEY,
                shirt TEXT NOT NULL,
                pant TEXT NOT NULL,
                shoes TEXT NOT NULL,
                rating INTEGER NOT NULL,
                UNIQUE(shirt, pant, shoes)
            )
        ''')
        
        # Check if rating exists for this outfit
        self.cursor.execute(
            "SELECT 1 FROM outfit_ratings WHERE shirt=? AND pant=? AND shoes=?",
            (shirt, pant, shoes))
        exists = self.cursor.fetchone()
        
        if exists:
            # Update existing rating
            self.cursor.execute(
                "UPDATE outfit_ratings SET rating=? WHERE shirt=? AND pant=? AND shoes=?",
                (self.current_rating, shirt, pant, shoes))
        else:
            # Insert new rating
            self.cursor.execute(
                "INSERT INTO outfit_ratings (shirt, pant, shoes, rating) VALUES (?, ?, ?, ?)",
                (shirt, pant, shoes, self.current_rating))
        
        self.conn.commit()
        messagebox.showinfo("Success", f"Outfit rating saved to {self.current_rating} stars")

    def update_outfit(self):
        """Open dialog to update outfit for selected date"""
        if not self.selected_date:
            return
        
        update_window = tk.Toplevel(self)
        update_window.title(f"Update Outfit for {self.selected_date.strftime('%Y-%m-%d')}")
        update_window.geometry("500x500")
        update_window.config(bg="#f8f9fa")
        
        # Get current outfit
        current_top = self.outfit_items['top']['text']
        current_bottom = self.outfit_items['bottom']['text']
        current_shoes = self.outfit_items['shoes']['text']
        
        # Get all available items
        self.cursor.execute("SELECT name, item_type FROM items")
        items = self.cursor.fetchall()
        
        tops = [name for name, typ in items if typ.lower() in ['shirt', 't-shirt', 'top']]
        bottoms = [name for name, typ in items if typ.lower() in ['pant', 'trouser', 'bottom']]
        shoes = [name for name, typ in items if typ.lower() in ['shoes', 'footwear']]
        
        # Create form
        form_frame = tk.Frame(update_window, bg="#f8f9fa")
        form_frame.pack(fill=tk.BOTH, padx=20, pady=20)
        
        # Top selection
        tk.Label(
            form_frame, text="Top Wear:", 
            font=("Segoe UI", 12), 
            bg="#f8f9fa", fg="#333333"
        ).pack(anchor="w", pady=(10, 5))
        
        top_var = tk.StringVar(value=current_top if current_top != "None" else "")
        top_combo = ttk.Combobox(
            form_frame, textvariable=top_var, 
            values=tops, font=("Segoe UI", 12)
        )
        top_combo.pack(fill=tk.X, pady=5)
        
        # Bottom selection
        tk.Label(
            form_frame, text="Bottom Wear:", 
            font=("Segoe UI", 12), 
            bg="#f8f9fa", fg="#333333"
        ).pack(anchor="w", pady=(10, 5))
        
        bottom_var = tk.StringVar(value=current_bottom if current_bottom != "None" else "")
        bottom_combo = ttk.Combobox(
            form_frame, textvariable=bottom_var, 
            values=bottoms, font=("Segoe UI", 12)
        )
        bottom_combo.pack(fill=tk.X, pady=5)
        
        # Shoes selection
        tk.Label(
            form_frame, text="Footwear:", 
            font=("Segoe UI", 12), 
            bg="#f8f9fa", fg="#333333"
        ).pack(anchor="w", pady=(10, 5))
        
        shoes_var = tk.StringVar(value=current_shoes if current_shoes != "None" else "")
        shoes_combo = ttk.Combobox(
            form_frame, textvariable=shoes_var, 
            values=shoes, font=("Segoe UI", 12)
        )
        shoes_combo.pack(fill=tk.X, pady=5)
        
        def save_outfit():
            """Save the updated outfit to database"""
            shirt = top_var.get() if top_var.get() else None
            pant = bottom_var.get() if bottom_var.get() else None
            shoes = shoes_var.get() if shoes_var.get() else None
            
            # Check if outfit already exists
            self.cursor.execute(
                "SELECT 1 FROM schedule WHERE day=?",
                (self.selected_date.strftime("%Y-%m-%d"),))
            exists = self.cursor.fetchone()
            
            if exists:
                # Update existing outfit
                self.cursor.execute(
                    "UPDATE schedule SET shirt=?, pant=?, shoes=? WHERE day=?",
                    (shirt, pant, shoes, self.selected_date.strftime("%Y-%m-%d")))
            else:
                # Insert new outfit
                self.cursor.execute(
                    "INSERT INTO schedule (day, shirt, pant, shoes) VALUES (?, ?, ?, ?)",
                    (self.selected_date.strftime("%Y-%m-%d"), shirt, pant, shoes)
                )
            
            self.conn.commit()
            update_window.destroy()
            self.show_day_details(0, 0)  # Refresh display
            self.update_calendar()  # Update calendar colors
        
        save_btn = GradientButton(
            form_frame, text="Save Outfit", command=save_outfit,
            color1=self.colors['primary'], color2=self.colors['secondary'],
            width=120, height=40, corner_radius=20
        )
        save_btn.pack(pady=20)

    def mark_as_worn(self):
        """Mark the selected outfit as worn (update wear count)"""
        if not self.selected_date:
            return
        
        # Get current outfit
        shirt = self.outfit_items['top']['text']
        pant = self.outfit_items['bottom']['text']
        shoes = self.outfit_items['shoes']['text']
        
        if shirt == "None" and pant == "None" and shoes == "None":
            messagebox.showwarning("Warning", "No outfit to mark as worn")
            return
        
        # Update wear count for each item
        for item_type, name in [('shirt', shirt), ('pant', pant), ('shoes', shoes)]:
            if name and name != "None":
                self.cursor.execute(
                    "UPDATE items SET wear_count = wear_count + 1 WHERE name=? AND item_type=?",
                    (name, item_type)
                )
        
        self.conn.commit()
        messagebox.showinfo("Success", "Outfit marked as worn")
        self.update_calendar()

    def prev_month(self):
        """Move to previous month"""
        first_day = self.current_date.replace(day=1)
        self.current_date = first_day - timedelta(days=1)
        self.update_calendar()

    def next_month(self):
        """Move to next month"""
        days_in_month = monthrange(self.current_date.year, self.current_date.month)[1]
        last_day = self.current_date.replace(day=days_in_month)
        self.current_date = last_day + timedelta(days=1)
        self.update_calendar()

    def show_today(self):
        """Show current month and today's date"""
        self.current_date = date.today()
        self.update_calendar()

    def update_calendar(self):
        """Update calendar display with schedule data"""
        # Load schedule data for the current period
        self.load_schedule_data()
        self.create_calendar_grid() 

    def truncate_text(self, text, max_length):
        """Truncate text with ellipsis if too long"""
        return text if len(text) <= max_length else text[:max_length-3] + "..."

    def quick_add_outfit(self):
        """Quickly add an outfit for today"""
        today = date.today()
        self.selected_date = today
        self.show_day_details_common()
        self.update_outfit()

    def get_outfit_suggestions(self):
        """Get outfit suggestions based on weather and trends"""
        # In a real app, this would use weather API and fashion trends
        suggestions = [
            "Light blue shirt with white jeans",
            "Black t-shirt with cargo pants",
            "Floral dress with sandals",
            "Denim jacket with khaki chinos"
        ]
        
        suggestion_window = tk.Toplevel(self)
        suggestion_window.title("Outfit Suggestions")
        suggestion_window.geometry("400x300")
        
        tk.Label(
            suggestion_window, text="Recommended Outfits", 
            font=("Segoe UI", 14, "bold"), pady=10
        ).pack()
        
        for suggestion in suggestions:
            tk.Label(
                suggestion_window, text=f"• {suggestion}", 
                font=("Segoe UI", 11), pady=5, anchor="w"
            ).pack(fill=tk.X, padx=20)
            
        tk.Button(
            suggestion_window, text="Apply Suggestion", 
            command=lambda: self.apply_suggestion(suggestions[0]),
            font=("Segoe UI", 11), pady=10
        ).pack(pady=10)

    def apply_suggestion(self, suggestion):
        """Apply a suggested outfit"""
        # This would parse the suggestion and set the outfit
        messagebox.showinfo("Success", "Outfit suggestion applied!")
        self.update_calendar()

class EnhancedScheduleView(tk.Toplevel):
    def __init__(self, parent, cursor, conn):
        super().__init__(parent)
        self.title("Enhanced Wardrobe Schedule")
        self.geometry("1200x800")
        self.cursor = cursor
        self.conn = conn
        self.configure(bg="#f8f9fa")
        
        # Create main container
        main_frame = tk.Frame(self, bg="#f8f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg="#f8f9fa")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            header_frame, text="Your Wardrobe Schedule", 
            font=("Segoe UI", 20, "bold"), 
            bg="#f8f9fa", fg="#2b2d42"
        ).pack(side=tk.LEFT)
        
        # Week navigation
        nav_frame = tk.Frame(header_frame, bg="#f8f9fa")
        nav_frame.pack(side=tk.RIGHT)
        
        prev_week_btn = GradientButton(
            nav_frame, text="◀ Prev Week", command=self.prev_week,
            color1="#4361ee", color2="#3a0ca3",
            width=120, height=35, corner_radius=15
        )
        prev_week_btn.pack(side=tk.LEFT, padx=5)
        
        next_week_btn = GradientButton(
            nav_frame, text="Next Week ▶", command=self.next_week,
            color1="#4361ee", color2="#3a0ca3",
            width=120, height=35, corner_radius=15
        )
        next_week_btn.pack(side=tk.LEFT, padx=5)
        
        # Schedule display
        schedule_frame = tk.Frame(main_frame, bg="#f8f9fa")
        schedule_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create day columns
        self.day_frames = []
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day in enumerate(day_names):
            day_frame = tk.Frame(
                schedule_frame, 
                bg="white",
                bd=1, relief=tk.RAISED,
                padx=10, pady=10
            )
            day_frame.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            day_frame.grid_propagate(False)
            
            # Day header
            tk.Label(
                day_frame, text=day, 
                font=("Segoe UI", 12, "bold"), 
                bg="white", fg="#2b2d42"
            ).pack(fill=tk.X, pady=(0, 10))
            
            # Date label
            date_label = tk.Label(
                day_frame, text="", 
                font=("Segoe UI", 10), 
                bg="white", fg="#8d99ae"
            )
            date_label.pack(fill=tk.X)
            
            # Outfit display
            outfit_frame = tk.Frame(day_frame, bg="white")
            outfit_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            self.day_frames.append({
                'frame': day_frame,
                'date_label': date_label,
                'outfit_frame': outfit_frame
            })
            
            # Configure grid weights
            schedule_frame.columnconfigure(i, weight=1)
        
        schedule_frame.rowconfigure(0, weight=1)
        
        # Load current week
        self.current_week = date.today()
        self.load_week_schedule()

    def load_week_schedule(self):
        """Load schedule for the current week"""
        # Calculate week start (Monday)
        week_start = self.current_week - timedelta(days=self.current_week.weekday())
        
        for i in range(7):
            current_date = week_start + timedelta(days=i)
            day_data = self.day_frames[i]

             # Get outfit from schedule table
            self.cursor.execute(
                "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
                (current_date.strftime("%Y-%m-%d"),))
            specific_outfit = self.cursor.fetchone()
            
            # If no specific date schedule, get weekly schedule
            if not specific_outfit:
                day_name = current_date.strftime("%A")
                self.cursor.execute(
                    "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
                    (day_name,))
                specific_outfit = self.cursor.fetchone()
            
            # Update date label
            day_data['date_label'].config(
                text=current_date.strftime("%b %d, %Y")
            )
            
            # Highlight today
            if current_date == date.today():
                day_data['frame'].config(bg="#e3f2fd")
            else:
                day_data['frame'].config(bg="white")
            
            # Clear previous outfit
            for widget in day_data['outfit_frame'].winfo_children():
                widget.destroy()
            
            # Get outfit for this day
            self.cursor.execute(
                "SELECT shirt, pant, shoes FROM schedule WHERE day=?",
                (current_date.strftime("%Y-%m-%d"),))
            outfit = self.cursor.fetchone()
            
            if outfit:
                shirt, pant, shoes = outfit
                
                # Display outfit items with icons
                if shirt:
                    self.add_outfit_item(
                        day_data['outfit_frame'], 
                        shirt, "icons/shirt.png", "Top"
                    )
                
                if pant:
                    self.add_outfit_item(
                        day_data['outfit_frame'], 
                        pant, "icons/pants.png", "Bottom"
                    )
                
                if shoes:
                    self.add_outfit_item(
                        day_data['outfit_frame'], 
                        shoes, "icons/shoes.png", "Shoes"
                    )
                
                # Add outfit rating
                self.cursor.execute(
                    "SELECT rating FROM outfit_ratings WHERE shirt=? AND pant=? AND shoes=?",
                    (shirt, pant, shoes)
                )
                rating = self.cursor.fetchone()
                
                if rating:
                    rating_frame = tk.Frame(day_data['outfit_frame'], bg="white")
                    rating_frame.pack(fill=tk.X, pady=(10, 0))
                    
                    tk.Label(
                        rating_frame, text="Rating:", 
                        font=("Segoe UI", 9), 
                        bg="white", fg="#8d99ae"
                    ).pack(side=tk.LEFT)
                    
                    for i in range(5):
                        color = "#FFD700" if i < rating[0] else "#cccccc"
                        tk.Label(
                            rating_frame, text="★", 
                            font=("Segoe UI", 12),
                            fg=color, bg="white"
                        ).pack(side=tk.LEFT)
            else:
                tk.Label(
                    day_data['outfit_frame'], text="No outfit scheduled", 
                    font=("Segoe UI", 10), 
                    bg="white", fg="#8d99ae"
                ).pack(pady=20)

    def add_weather_info(self, parent, outfit_date):
        """Add weather forecast to outfit cards"""
        try:
            # Get weather data (mock implementation - replace with real API)
            weather = self.get_weather_forecast(outfit_date)
            
            if weather:
                weather_frame = ttk.Frame(parent, style="TFrame")
                weather_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
                
                # Weather icon
                weather_icon = "☀️" if weather["temp"] > 20 else "🌧️" if weather["precip"] > 0 else "⛅"
                tk.Label(
                    weather_frame, text=weather_icon,
                    font=("Segoe UI", 14),
                    bg="white"
                ).pack(side=tk.LEFT, padx=(0, 5))
                
                # Weather details
                details = f"{weather['temp']}°C | {weather['condition']}"
                tk.Label(
                    weather_frame, text=details,
                    font=("Segoe UI", 9),
                    bg="white", fg="#8d99ae"
                ).pack(side=tk.LEFT)
                
                # Weather suitability indicator
                suitability = self.calculate_weather_suitability(weather)
                canvas = tk.Canvas(weather_frame, width=80, height=20, bg="white", highlightthickness=0)
                canvas.pack(side=tk.RIGHT)
                
                # Draw suitability meter
                canvas.create_rectangle(0, 0, 80, 20, outline="#e0e0e0", fill="white")
                canvas.create_rectangle(0, 0, suitability*80, 20, outline="#4CAF50", fill="#4CAF50")
                canvas.create_text(40, 10, text=f"{suitability*100:.0f}%", fill="white", font=("Segoe UI", 9))
        except Exception as e:
            print(f"Weather display error: {e}")

    def get_weather_forecast(self, date):
        """Mock weather data - replace with real API call"""
        # This would normally call a weather API
        return {
            "temp": random.randint(10, 30),
            "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]),
            "precip": random.random(),
            "humidity": random.randint(30, 90)
        }

    def calculate_weather_suitability(self, weather):
        """Calculate how suitable the outfit is for the weather"""
        # Simple mock calculation - expand with real logic
        base_score = 0.7
        if weather["temp"] > 25:
            base_score -= 0.1
        if weather["precip"] > 0.5:
            base_score -= 0.2
        return max(0.3, min(1.0, base_score + random.uniform(-0.1, 0.1)))

    def add_outfit_score(self, parent, shirt, pant, shoes):
        """Add visual outfit scoring"""
        try:
            # Calculate outfit score (replace with your scoring logic)
            score = self.calculate_outfit_score(shirt, pant, shoes)
            
            score_frame = ttk.Frame(parent, style="TFrame")
            score_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            tk.Label(
                score_frame, text="Style Score:",
                font=("Segoe UI", 9),
                bg="white", fg="#8d99ae"
            ).pack(side=tk.LEFT)
            
            # Visual score meter
            canvas = tk.Canvas(score_frame, width=100, height=20, bg="white", highlightthickness=0)
            canvas.pack(side=tk.RIGHT)
            
            # Draw gradient meter
            for i in range(100):
                r = int(255 * (1 - i/100))
                g = int(255 * (i/100))
                b = 0
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_line(i, 0, i, 20, fill=color)
            
            # Draw score indicator
            canvas.create_rectangle(score*100-2, 0, score*100+2, 20, outline="white", fill="white")
            canvas.create_text(score*100, 10, text=f"{score*100:.0f}", fill="white", font=("Segoe UI", 8))
            
        except Exception as e:
            print(f"Score display error: {e}")

    def calculate_outfit_score(self, shirt, pant, shoes):
        """Calculate outfit score based on various factors"""
        # Get item details from database
        items = []
        for name in [shirt, pant, shoes]:
            if name:
                self.cursor.execute(
                    "SELECT color, fabric, wear_count FROM items WHERE name=?",
                    (name,))
                item = self.cursor.fetchone()
                if item:
                    items.append({
                        "color": item[0],
                        "fabric": item[1],
                        "wear_count": item[2]
                    })
        
        # Simple scoring logic (expand with your rules)
        score = 0.5  # Base score
        
        # Color harmony
        if len(items) >= 2:
            color1 = items[0]["color"].lower()
            color2 = items[1]["color"].lower()
            if color1 in self.color_palettes.get(color2, []):
                score += 0.2
        
        # Fabric compatibility
        fabrics = [item["fabric"].lower() for item in items]
        if "denim" in fabrics and "cotton" in fabrics:
            score += 0.1
        
        # Wear count balancing
        wear_counts = [item["wear_count"] for item in items if "wear_count" in item]
        if wear_counts:
            avg_wear = sum(wear_counts)/len(wear_counts)
            score += min(0.1, (10 - avg_wear) * 0.01)
        
        return min(1.0, max(0.3, score))

    def add_context_menu(self, widget):
        """Add right-click context menu"""
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Edit Outfit", command=lambda: self.edit_outfit(widget.date))
        menu.add_command(label="Mark as Worn", command=lambda: self.mark_as_worn(widget.date))
        menu.add_command(label="Copy to Clipboard")
        
        def show_menu(e):
            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()
        
        widget.bind("<Button-3>", show_menu)

    def create_daily_reminder(self):
        """Add daily reminder notification"""
        reminder_frame = ttk.Frame(self.schedule_frame, style="Accent.TFrame")
        reminder_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(
            reminder_frame, 
            text="🔔 Don't forget to plan tomorrow's outfit!",
            font=("Segoe UI", 11),
            bg="#f72585", fg="white"
        ).pack(pady=5)
        
        # Add pulsing animation
        self.animate_pulse_reminder(reminder_frame)

    def animate_pulse_reminder(self, widget):
        """Continuous pulse animation for reminders"""
        def pulse():
            if widget.winfo_exists():
                current_bg = widget.cget("background")
                if current_bg == "#f72585":
                    widget.config(background="#ff4081")
                else:
                    widget.config(background="#f72585")
                widget.after(1000, pulse)
        
        pulse()

    def add_quick_stats(self):
        """Add quick statistics panel"""
        stats_frame = ttk.Frame(self.schedule_frame, style="Card.TFrame")
        stats_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Calculate stats
        scheduled_days = len([d for d in self.day_frames if self.schedule_data.get(d['date'].strftime("%Y-%m-%d"))])
        total_items = sum(1 for d in self.day_frames if self.schedule_data.get(d['date'].strftime("%Y-%m-%d")))
        
        stats = [
            ("📅 Scheduled Days", f"{scheduled_days}/7"),
            ("👕 Planned Items", str(total_items)),
            ("⭐ Avg Rating", "4.2"),
            ("☀️ Best Weather Day", "Wednesday")
        ]
        
        for i, (label, value) in enumerate(stats):
            stat_frame = ttk.Frame(stats_frame, style="TFrame")
            stat_frame.grid(row=0, column=i, padx=10, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            
            tk.Label(
                stat_frame, text=label,
                font=("Segoe UI", 9),
                bg="white", fg="#8d99ae"
            ).pack()
            
            tk.Label(
                stat_frame, text=value,
                font=("Segoe UI", 12, "bold"),
                bg="white", fg="#2b2d42"
            ).pack()            

    def add_outfit_item(self, parent, item_name, icon_path, item_type):
        """Add an outfit item to the display"""
        item_frame = tk.Frame(parent, bg="white")
        item_frame.pack(fill=tk.X, pady=3)
        
        # Icon
        try:
            icon_img = Image.open(icon_path)
            icon_img = icon_img.resize((20, 20), Image.LANCZOS)
            icon = ImageTk.PhotoImage(icon_img)
            icon_label = tk.Label(item_frame, image=icon, bg="white")
            icon_label.image = icon
            icon_label.pack(side=tk.LEFT, padx=(0, 5))
        except:
            pass
        
        # Item details
        self.cursor.execute(
            "SELECT color, fabric FROM items WHERE name=?",
            (item_name,)
        )
        item_data = self.cursor.fetchone()
        
        if item_data:
            color, fabric = item_data
            details = f"{item_name}\n{color}, {fabric}"
        else:
            details = item_name
        
        tk.Label(
            item_frame, text=details, 
            font=("Segoe UI", 9), 
            bg="white", fg="#2b2d42",
            justify=tk.LEFT
        ).pack(side=tk.LEFT)

    def prev_week(self):
        """Move to previous week"""
        self.current_week = self.current_week - timedelta(days=7)
        self.load_week_schedule()

    def next_week(self):
        """Move to next week"""
        self.current_week = self.current_week + timedelta(days=7)
        self.load_week_schedule()

class ModernButton(tk.Canvas):
    def __init__(self, master, text, command, color1, color2, icon=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.color1 = color1
        self.color2 = color2
        self.text = text
        self.icon = icon
        self.width = 250  # Increased base width
        self.height = 70   # Increased base height
        self.corner_radius = 20
        self.hover = False
        self.config(width=self.width, height=self.height, 
                   bd=0, highlightthickness=0, bg="#F5F7FA")
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Configure>", self.on_resize)  # Handle window resize
        
        self.draw_button()
    
    def on_resize(self, event):
        """Resize button when window changes size"""
        # Only resize if the change is significant
        if event.width > self.width + 20 or event.width < self.width - 20:
            self.width = max(250, min(350, event.width))  # Set min/max sizes
            self.height = max(70, min(90, self.height))
            self.draw_button()
        
    def draw_button(self):
        self.delete("all")
        
        # Create gradient background
        for i in range(self.height):
            ratio = i / self.height
            r = int(self.color1[0] * (1 - ratio) + self.color2[0] * ratio)
            g = int(self.color1[1] * (1 - ratio) + self.color2[1] * ratio)
            b = int(self.color1[2] * (1 - ratio) + self.color2[2] * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.create_line(0, i, self.width, i, fill=color)
        
        # Add rounded corners
        self.create_oval(0, 0, self.corner_radius*2, self.corner_radius*2, 
                         fill=self.get_avg_color(), outline="")
        self.create_oval(self.width - self.corner_radius*2, 0, self.width, self.corner_radius*2, 
                         fill=self.get_avg_color(), outline="")
        self.create_oval(0, self.height - self.corner_radius*2, self.corner_radius*2, self.height, 
                         fill=self.get_avg_color(), outline="")
        self.create_oval(self.width - self.corner_radius*2, self.height - self.corner_radius*2, 
                         self.width, self.height, fill=self.get_avg_color(), outline="")
        
        # Create the hover effect (slight overlay)
        if self.hover:
            self.create_rectangle(0, 0, self.width, self.height, 
                                 fill="white", stipple="gray25", outline="")
        
        # Add text
        text_color = "#FFFFFF" if self.get_brightness() < 150 else "#2C3E50"
        font_size = max(12, min(16, int(self.width / 20)))  # Responsive font size
        self.create_text(self.width/2, self.height/2, text=self.text, 
                        fill=text_color, font=("Segoe UI", font_size, "bold"))
        
        # Add icon if provided
        if self.icon:
            try:
                img = Image.open(self.icon)
                icon_size = max(24, min(32, int(self.width / 12)))  # Responsive icon
                img = img.resize((icon_size, icon_size), Image.LANCZOS)
                icon = ImageTk.PhotoImage(img)
                self.icon_img = icon  # Keep reference
                self.create_image(30, self.height/2, image=icon, anchor="w")
            except:
                pass
    
    def get_avg_color(self):
        r = (self.color1[0] + self.color2[0]) // 2
        g = (self.color1[1] + self.color2[1]) // 2
        b = (self.color1[2] + self.color2[2]) // 2
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def get_brightness(self):
        r, g, b = self.color1
        return (r * 299 + g * 587 + b * 114) // 1000
    
    def on_enter(self, event):
        self.hover = True
        self.draw_button()
        
    def on_leave(self, event):
        self.hover = False
        self.draw_button()
        
    def on_click(self, event):
        self.command()
        # Add click animation
        self.create_oval(event.x-10, event.y-10, event.x+10, event.y+10, 
                        fill="white", outline="", tags="ripple")
        self.after(50, lambda: self.delete("ripple"))


class WardrobeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wardrobe Manager Pro")
        self.root.geometry("1300x900")  # Slightly larger initial size
        self.root.config(bg="#F5F7FA")
        self.root.minsize(1100, 750)  # Set minimum window size
        
        # Make the UI responsive
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Custom Fonts
        self.title_font = ("Segoe UI", 36, "bold")  # Larger title
        self.subtitle_font = ("Segoe UI", 16)  # Larger subtitle
        self.button_font = ("Segoe UI", 14, "bold")
        self.label_font = ("Segoe UI", 12)
        self.dashboard_font = ("Segoe UI", 18, "bold")

        self.color_palettes = {
            "red": ["black", "white", "navy", "gold"],
            "blue": ["white", "navy", "gray", "brown", "red"],
            "green": ["brown", "khaki", "black", "white"],
            "yellow": ["gray", "white", "navy", "black"],
            "black": ["white", "red", "blue", "yellow", "pink", "gray", "silver"],
            "white": ["black", "red", "blue", "green", "yellow", "pink"],
            "pink": ["black", "white", "gray", "navy"],
            "gray": ["black", "white", "pink", "blue", "red"],
            "orange": ["blue", "white", "black"],
            "brown": ["white", "blue", "green", "beige"],
            "purple": ["white", "black", "gray", "yellow"],
            "cyan": ["black", "white", "gray", "navy"]
        }
    
        # Add trending colors/fabrics for scoring
        self.trending_colors = ["navy", "sage green", "cream white"]
        self.trending_fabrics = ["Khadi", "Linen", "Organic Cotton"]
            
        # Create a container frame that expands with the window
        self.main_container = tk.Frame(root, bg="#F5F7FA")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Header Section
        self.header_frame = tk.Frame(self.main_container, bg="#F5F7FA")
        self.header_frame.pack(fill=tk.X, pady=(0, 30))  # More padding
        
        # Title with shadow effect
        title_frame = tk.Frame(self.header_frame, bg="#F5F7FA")
        title_frame.pack()
        
        # Main title
        tk.Label(title_frame, text="👔 Wardrobe Manager Pro", 
                font=self.title_font, fg="#2C3E50", bg="#FAF5F5").pack()
        
        # Subtitle with more space
        tk.Label(title_frame, text="Organize • Style • Discover", 
                font=self.subtitle_font, fg="#7F8C8D", bg="#F5F7FA").pack(pady=(10, 20))

        # Button Grid Section - Using grid for better responsiveness
        self.button_grid = tk.Frame(self.main_container, bg="#F5F7FA")
        self.button_grid.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid to expand with minimum sizes
        for i in range(3):  # 3 columns
            self.button_grid.columnconfigure(i, weight=1, minsize=300, uniform="cols")
        for i in range(4):  # 4 rows
            self.button_grid.rowconfigure(i, weight=1, minsize=100, uniform="rows")

        # Modern color scheme for buttons
        button_colors = [
            ((52, 152, 219), (41, 128, 185)),    # Blue
            ((46, 204, 113), (39, 174, 96)),     # Green
            ((155, 89, 182), (142, 68, 173)),    # Purple
            ((241, 196, 15), (243, 156, 18)),    # Yellow
            ((230, 126, 34), (211, 84, 0)),      # Orange
            ((22, 160, 133), (20, 143, 119)),    # Teal
            ((52, 73, 94), (44, 62, 80)),        # Dark Blue
            ((149, 165, 166), (127, 140, 141)),  # Gray
            ((26, 188, 156), (22, 160, 133)),    # Turquoise
            ((231, 76, 60), (192, 57, 43)),       # Red
            ((230, 126, 34), (211, 84, 0))     # Orange
        ]
        
        # Button Configuration
        buttons = [
            ("Add New Item", self.add_item, button_colors[0], "add_icon.png", 0, 0),
            ("View Inventory", self.show_items, button_colors[1], "show_icon.png", 0, 1),
            ("Generate Schedule", self.schedulize, button_colors[2], "schedule_icon.png", 0, 2),
            ("View Schedule", self.open_schedule_page, button_colors[3], "open_icon.png", 1, 0),
            ("View Calendar", self.show_calendar, button_colors[4], "icons/calendar.png", 1, 1),
            ("Advanced Search", self.search_items, button_colors[5], "search_icon.png", 1, 2),
            ("Expense Tracker", self.expense_tracker, button_colors[6], "expense_icon.png", 2, 0),
            ("Backup Data", self.backup_data, button_colors[7], "backup_icon.png", 2, 1),
            ("Wardrobe Analytics", self.open_dashboard, button_colors[8], "dashboard_icon.png", 2, 2),
            ("Weather Suggestions", self.weather_suggestions, button_colors[9], "weather_icon.png", 3, 0),
            ("Exit Application", self.root.quit, button_colors[10], "exit_icon.png", 3,2)
        ]

        # Create modern buttons with proper spacing
        self.button_widgets = []
        for text, command, colors, icon, row, col in buttons:
            color1, color2 = colors
            btn = ModernButton(
                self.button_grid, 
                text=text, 
                command=command,
                color1=color1,
                color2=color2,
                icon=icon,
                width=300,  # Wider buttons
                height=80   # Taller buttons
            )
            
            # Position in grid with proper spacing
            if row == 3 and col == 1:  # Center the Exit button
                btn.grid(row=row, column=0, columnspan=3, padx=20, pady=20, sticky="nsew")
            else:
                btn.grid(row=row, column=col, padx=20, pady=20, sticky="nsew")
            
            self.button_widgets.append(btn)

        # Initialize database connection
        self.conn = sqlite3.connect('wardrobe.db')
        self.cursor = self.conn.cursor()
        
        # Setup database
        self.db_setup()

        # Weather API
        self.weather_api_key = "ed3fd15a9b81d0193b1722f486de6243"
        
        # Add footer
        footer = tk.Label(self.root, text="Wardrobe Manager Pro © 2023 | Stay Stylish", 
                         font=("Segoe UI", 10), fg="#7F8C8D", bg="#F5F7FA")
        footer.pack(side=tk.BOTTOM, pady=20)
        
        # Add subtle shadow to buttons
        self.add_button_shadows()
    
    def show_calendar(self):
        """Show the enhanced calendar view"""
        CalendarView(self.root, self.cursor, self.conn)

    def open_schedule_page(self):
        """Show the enhanced schedule view"""
        EnhancedScheduleView(self.root, self.cursor, self.conn)    
       
    def add_button_shadows(self):
        """Add subtle shadows to buttons for depth"""
        for btn in self.button_widgets:
            shadow = tk.Frame(btn.master, bg="#D5DBDB")
            shadow.place(in_=btn, x=3, y=3, relwidth=1, relheight=1)
            shadow.lower(btn)

    def on_window_resize(self, event):
        """Adjust button sizes when window is resized"""
        # Calculate proportional font size based on window width
        width = self.root.winfo_width()
        base_font_size = max(10, min(14, int(width / 80)))
        
        # Update button fonts
        for btn in self.buttons:
            btn.config(font=("Segoe UI", base_font_size, "bold"))
            
        # Update icon sizes
        for btn in self.buttons:
            if hasattr(btn, 'image'):
                # Recreate icon with proportional size
                icon_path = btn.image.filename if hasattr(btn.image, 'filename') else ""
                if icon_path:
                    try:
                        size = max(16, min(24, int(width / 60)))
                        img = Image.open(icon_path)
                        img = img.resize((size, size), Image.LANCZOS)
                        icon_img = ImageTk.PhotoImage(img)
                        btn.config(image=icon_img)
                        btn.image = icon_img  # Keep reference
                    except:
                        pass

    def db_setup(self):      
        try:
            # Create items table (existing)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    color TEXT NOT NULL,
                    fabric TEXT NOT NULL,
                    wear_count INTEGER DEFAULT 0,
                    purchase_price REAL DEFAULT 0,
                    purchase_date TEXT,
                    UNIQUE(name, item_type, color, fabric)
                )
            ''')

            # Create schedule table (existing)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY,
                    day TEXT NOT NULL,
                    shirt TEXT,
                    pant TEXT,
                    shoes TEXT
                )
            ''')
            
            # Create outfit_ratings table (new)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS outfit_ratings (
                    id INTEGER PRIMARY KEY,
                    shirt TEXT NOT NULL,
                    pant TEXT NOT NULL,
                    shoes TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    UNIQUE(shirt, pant, shoes)
                )
            ''')

            # Create expenses table (new)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY,
                    item_id INTEGER,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY(item_id) REFERENCES items(id)
                )
            ''')

            # Create budget table (new)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS budget (
                    id INTEGER PRIMARY KEY,
                    category TEXT UNIQUE NOT NULL,
                    monthly_limit REAL NOT NULL,
                    current_spending REAL DEFAULT 0
                )
            ''')

            self.conn.commit()
            print("Database tables initialized successfully")
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")
        except Exception as e:
            print(f"General error: {e}")

    def expense_tracker(self):
        """Advanced Expense Tracker with Modern UI and Smart Features"""
        expense_win = tk.Toplevel(self.root)
        expense_win.title("💰 Wardrobe Finance Pro")
        expense_win.geometry("1400x900")
        expense_win.configure(bg="#f5f7fa")
        
        # Modern styling
        style = ttk.Style()
        style.configure("TNotebook", background="#ffffff")
        style.configure("TFrame", background="#ffffff")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.map("TButton", background=[("active", "#e1e5ea")])
        
        # Header Frame
        header_frame = tk.Frame(expense_win, bg="#4a6fa5", height=80)
        header_frame.pack(fill="x")
        tk.Label(header_frame, 
                text="WARDROBE FINANCE DASHBOARD", 
                font=("Segoe UI", 18, "bold"), 
                bg="#4a6fa5", 
                fg="white").pack(pady=20)
        
        # Main Container
        main_frame = tk.Frame(expense_win, bg="#f5f7fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Notebook with modern tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        # ========== TAB 1: Smart Expense Log ==========
        log_frame = ttk.Frame(notebook, style="TFrame")
        notebook.add(log_frame, text="➕ Log Expense")
        
        # Form with modern cards
        form_card = tk.Frame(log_frame, bg="white", bd=0, highlightthickness=0, 
                            relief="solid", padx=20, pady=20)
        form_card.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Auto-sync with items table
        def sync_item_data():
            self.cursor.execute("SELECT name, purchase_price, purchase_date FROM items WHERE purchase_price > 0")
            return self.cursor.fetchall()
        
        # Item Selection with autocomplete
        tk.Label(form_card, text="Item Purchased", font=("Segoe UI", 10, "bold"), bg="white").grid(row=0, column=0, sticky="w", pady=(0,5))
        item_var = tk.StringVar()
        item_combo = ttk.Combobox(form_card, textvariable=item_var, font=("Segoe UI", 10), width=30)
        item_combo.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Auto-fill price and date when item selected
        def on_item_select(event):
            selected = item_var.get()
            for name, price, p_date in sync_item_data():
                if name == selected:
                    amount_var.set(f"{price:.2f}")
                    date_var.set(p_date)
                    break
        
        item_combo.bind("<<ComboboxSelected>>", on_item_select)
        item_combo['values'] = [item[0] for item in sync_item_data()]
        
        # Date with modern calendar
        tk.Label(form_card, text="Date", font=("Segoe UI", 10, "bold"), bg="white").grid(row=0, column=1, sticky="w", pady=(0,5))
        date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(form_card, textvariable=date_var, font=("Segoe UI", 10))
        date_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        def show_calendar():
            cal_win = tk.Toplevel()
            cal_win.title("Select Date")
            cal = Calendar(cal_win, selectmode='day', date_pattern='y-mm-dd')
            cal.pack(pady=10)
            ttk.Button(cal_win, text="Select", command=lambda: [
                date_var.set(cal.get_date()),
                cal_win.destroy()
            ]).pack()
        
        ttk.Button(form_card, text="📅", command=show_calendar, width=3).grid(row=1, column=2, padx=(0,5))
        
        # Amount
        tk.Label(form_card, text="Amount ($)", font=("Segoe UI", 10, "bold"), bg="white").grid(row=2, column=0, sticky="w", pady=(10,5))
        amount_var = tk.StringVar()
        ttk.Entry(form_card, textvariable=amount_var, font=("Segoe UI", 10)).grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        # Category with icons
        tk.Label(form_card, text="Category", font=("Segoe UI", 10, "bold"), bg="white").grid(row=2, column=1, sticky="w", pady=(10,5))
        categories = {
            "👕 Clothing": "Clothing",
            "👟 Footwear": "Footwear",
            "🧣 Accessories": "Accessories",
            "🧼 Maintenance": "Maintenance",
            "🧺 Laundry": "Laundry",
            "📦 Other": "Other"
        }
        category_combo = ttk.Combobox(form_card, values=list(categories.keys()), font=("Segoe UI", 10))
        category_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        category_combo.current(0)
        
        # Payment Method
        tk.Label(form_card, text="Payment Method", font=("Segoe UI", 10, "bold"), bg="white").grid(row=4, column=0, sticky="w", pady=(10,5))
        payment_methods = ["💵 Cash", "💳 Credit Card", "🏦 Debit Card", "📱 PayPal", "🔄 Bank Transfer"]
        payment_combo = ttk.Combobox(form_card, values=payment_methods, font=("Segoe UI", 10))
        payment_combo.grid(row=5, column=0, sticky="ew", padx=5, pady=5)
        payment_combo.current(1)
        
        # Receipt Upload
        tk.Label(form_card, text="Receipt (Optional)", font=("Segoe UI", 10, "bold"), bg="white").grid(row=4, column=1, sticky="w", pady=(10,5))
        receipt_frame = tk.Frame(form_card, bg="white")
        receipt_frame.grid(row=5, column=1, sticky="ew", padx=5)
        
        def upload_receipt():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
            if file_path:
                receipt_label.config(text=f"📄 {os.path.basename(file_path)}")
        
        ttk.Button(receipt_frame, text="Upload", command=upload_receipt, width=8).pack(side="left")
        receipt_label = tk.Label(receipt_frame, text="No file selected", bg="white", fg="#666")
        receipt_label.pack(side="left", padx=5)
        
        # Notes
        tk.Label(form_card, text="Notes", font=("Segoe UI", 10, "bold"), bg="white").grid(row=6, column=0, columnspan=2, sticky="w", pady=(10,5))
        notes_text = tk.Text(form_card, height=4, width=40, font=("Segoe UI", 10), bd=1, relief="solid")
        notes_text.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Save Button with modern style
        save_btn = tk.Button(form_card, text="💾 Save Expense", 
                            command=lambda: self.save_expense(
                                item_var.get(),
                                categories[category_combo.get()],
                                float(amount_var.get()),
                                date_var.get(),
                                payment_combo.get(),
                                notes_text.get("1.0", tk.END).strip()
                            ),
                            bg="#4CAF50", fg="white", bd=0, padx=15, pady=8,
                            font=("Segoe UI", 10, "bold"))
        save_btn.grid(row=8, column=0, columnspan=2, pady=15)
        
        # ========== TAB 2: Financial Dashboard ==========
        dashboard_frame = ttk.Frame(notebook)
        notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Summary Cards
        cards_frame = tk.Frame(dashboard_frame, bg="#f5f7fa")
        cards_frame.pack(fill="x", pady=10)
        
        def create_summary_card(parent, title, value, color):
            card = tk.Frame(parent, bg="white", bd=0, highlightthickness=0, relief="solid", padx=15, pady=10)
            tk.Label(card, text=title, bg="white", fg="#666", font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(card, text=value, bg="white", fg=color, font=("Segoe UI", 14, "bold")).pack(anchor="w")
            return card
        
        # Calculate financial metrics
        def calculate_financial_metrics():
            # Total spending
            self.cursor.execute("SELECT SUM(purchase_price) FROM items")
            total_spending = self.cursor.fetchone()[0] or 0
            
            # Monthly spending
            current_month = datetime.datetime.now().strftime("%Y-%m")
            self.cursor.execute("SELECT SUM(purchase_price) FROM items WHERE strftime('%Y-%m', purchase_date) = ?", (current_month,))
            monthly_spending = self.cursor.fetchone()[0] or 0
            
            # Average monthly spending
            self.cursor.execute("SELECT strftime('%Y-%m', purchase_date) as month, SUM(purchase_price) as monthly_total FROM items GROUP BY month")
            monthly_totals = self.cursor.fetchall()
            avg_monthly = sum(row[1] for row in monthly_totals)/len(monthly_totals) if monthly_totals else 0
            
            # Top category
            self.cursor.execute("SELECT item_type, SUM(purchase_price) as total FROM items GROUP BY item_type ORDER BY total DESC LIMIT 1")
            top_category = self.cursor.fetchone()
            top_category_name = top_category[0] if top_category else "N/A"
            
            # Budget status (assuming budget is set)
            self.cursor.execute("SELECT SUM(monthly_limit) FROM budget")
            total_budget = self.cursor.fetchone()[0] or 0
            budget_status = "On Track" if monthly_spending <= total_budget else "Over Budget"
            
            return {
                "total_spending": total_spending,
                "monthly_spending": monthly_spending,
                "avg_monthly": avg_monthly,
                "top_category": top_category_name,
                "budget_status": budget_status
            }
        
        metrics = calculate_financial_metrics()
        
        # Add cards to dashboard
        monthly_spent_card = create_summary_card(cards_frame, "Monthly Spend", f"${metrics['monthly_spending']:.2f}", "#E53935")
        monthly_spent_card.pack(side="left", padx=5, ipadx=20)
        
        budget_status_card = create_summary_card(cards_frame, "Budget Status", metrics['budget_status'], 
                                            "#43A047" if metrics['budget_status'] == "On Track" else "#E53935")
        budget_status_card.pack(side="left", padx=5, ipadx=20)
        
        top_category_card = create_summary_card(cards_frame, "Top Category", metrics['top_category'], "#1E88E5")
        top_category_card.pack(side="left", padx=5, ipadx=20)
        
        avg_spend_card = create_summary_card(cards_frame, "Avg. Monthly", f"${metrics['avg_monthly']:.2f}", "#FB8C00")
        avg_spend_card.pack(side="left", padx=5, ipadx=20)
        
        total_spend_card = create_summary_card(cards_frame, "Total Spending", f"${metrics['total_spending']:.2f}", "#9C27B0")
        total_spend_card.pack(side="left", padx=5, ipadx=20)
        
        # Spending Trends Frame
        trends_frame = tk.Frame(dashboard_frame, bg="white", bd=1, relief=tk.GROOVE)
        trends_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(trends_frame, text="📈 Spending Trends", font=("Segoe UI", 12, "bold"), bg="white").pack(pady=10)
        
        # Create a canvas for the spending chart with a fixed height
        chart_container = tk.Frame(trends_frame, bg="white")
        chart_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        chart_canvas = tk.Canvas(chart_container, bg="white", height=250)
        chart_canvas.pack(fill="both", expand=True)
        
        # Draw spending trends chart
        def draw_spending_chart(width=None):
            if width is None:
                width = chart_canvas.winfo_width() - 40
                
            # Clear previous drawing
            chart_canvas.delete("all")
            
            # Get monthly spending data
            self.cursor.execute("""
                SELECT strftime('%Y-%m', purchase_date) as month, 
                    SUM(purchase_price) as total 
                FROM items 
                GROUP BY month 
                ORDER BY month
            """)
            monthly_data = self.cursor.fetchall()
            
            if not monthly_data:
                chart_canvas.create_text(150, 100, text="No spending data available", font=("Segoe UI", 12))
                return
            
            months = [row[0] for row in monthly_data]
            amounts = [row[1] for row in monthly_data]
            max_amount = max(amounts) if amounts else 1
            
            # Calculate chart dimensions
            height = 200
            bar_width = width / len(months) * 0.8
            gap = width / len(months) * 0.2
            
            # Draw axes
            chart_canvas.create_line(30, height-30, width+30, height-30, width=2)  # X-axis
            chart_canvas.create_line(30, 30, 30, height-30, width=2)  # Y-axis
            
            # Draw Y-axis labels
            for i in range(0, 6):
                y = height-30 - (i * (height-60) / 5)
                value = max_amount * i / 5
                chart_canvas.create_text(20, y, text=f"${value:.0f}", anchor="e", font=("Segoe UI", 8))
            
            # Draw bars for each month
            for i, (month, amount) in enumerate(zip(months, amounts)):
                x1 = 30 + i * (bar_width + gap)
                x2 = x1 + bar_width
                y = height-30 - (amount/max_amount) * (height-60)
                
                # Draw bar
                chart_canvas.create_rectangle(x1, y, x2, height-30, fill="#4a6fa5", outline="")
                
                # Draw month label (rotated)
                chart_canvas.create_text(x1 + bar_width/2, height-15, text=month, 
                                    angle=45, anchor="nw", font=("Segoe UI", 8))
                
                # Draw amount on top of bar
                chart_canvas.create_text(x1 + bar_width/2, y-5, text=f"${amount:.0f}", 
                                    anchor="s", font=("Segoe UI", 8))
        
        # Draw chart initially
        draw_spending_chart()
        
        # Redraw chart on resize
        def on_canvas_resize(event):
            draw_spending_chart(width=event.width - 40)
        
        chart_canvas.bind("<Configure>", on_canvas_resize)
        
        # ========== TAB 3: Budget Manager ==========
        budget_frame = ttk.Frame(notebook)
        notebook.add(budget_frame, text="🧾 Budgets")
        
        # Budget Treeview with modern styling
        budget_tree = ttk.Treeview(budget_frame, columns=("Category", "Budget", "Spent", "Remaining", "Status"), 
                                show="headings", height=12)
        budget_tree.heading("Category", text="Category")
        budget_tree.heading("Budget", text="Budget ($)")
        budget_tree.heading("Spent", text="Spent ($)")
        budget_tree.heading("Remaining", text="Remaining ($)")
        budget_tree.heading("Status", text="Status")
        budget_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Populate budget tree
        def populate_budget_tree():
            # Clear existing items
            for item in budget_tree.get_children():
                budget_tree.delete(item)
            
            # Get budget data
            self.cursor.execute("""
                SELECT b.category, b.monthly_limit, 
                    COALESCE(SUM(i.purchase_price), 0) as spent,
                    b.monthly_limit - COALESCE(SUM(i.purchase_price), 0) as remaining
                FROM budget b
                LEFT JOIN items i ON b.category = i.item_type 
                    AND strftime('%Y-%m', i.purchase_date) = strftime('%Y-%m', 'now')
                GROUP BY b.category
            """)
            
            for row in self.cursor.fetchall():
                category, budget, spent, remaining = row
                status = "Under" if remaining >= 0 else "Over"
                budget_tree.insert("", tk.END, values=(category, f"${budget:.2f}", 
                                                    f"${spent:.2f}", f"${remaining:.2f}", status))
        
        populate_budget_tree()
        
        # Budget Controls
        control_frame = tk.Frame(budget_frame, bg="#f5f7fa")
        control_frame.pack(fill="x", pady=5)
        
        tk.Label(control_frame, text="Set Budget:", bg="#f5f7fa").pack(side="left", padx=5)
        budget_category_combo = ttk.Combobox(control_frame, values=["Clothing", "Footwear", "Accessories", "Maintenance", "Laundry", "Other"])
        budget_category_combo.pack(side="left", padx=5)
        
        tk.Label(control_frame, text="$", bg="#f5f7fa").pack(side="left", padx=5)
        budget_amount_entry = ttk.Entry(control_frame, width=10)
        budget_amount_entry.pack(side="left", padx=5)
        
        def update_budget():
            category = budget_category_combo.get()
            try:
                amount = float(budget_amount_entry.get())
                # Check if budget already exists
                self.cursor.execute("SELECT 1 FROM budget WHERE category=?", (category,))
                exists = self.cursor.fetchone()
                
                if exists:
                    self.cursor.execute("UPDATE budget SET monthly_limit=? WHERE category=?", (amount, category))
                else:
                    self.cursor.execute("INSERT INTO budget (category, monthly_limit) VALUES (?, ?)", (category, amount))
                
                self.conn.commit()
                messagebox.showinfo("Success", f"Budget for {category} set to ${amount:.2f}")
                populate_budget_tree()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")
        
        ttk.Button(control_frame, text="Update Budget", command=update_budget).pack(side="left", padx=10)
        
        # ========== TAB 4: Expense History ==========
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="📑 Expense History")
        
        # Expense Treeview
        expense_tree = ttk.Treeview(history_frame, columns=("Date", "Item", "Category", "Amount", "Notes"), 
                                show="headings", height=15)
        expense_tree.heading("Date", text="Date")
        expense_tree.heading("Item", text="Item")
        expense_tree.heading("Category", text="Category")
        expense_tree.heading("Amount", text="Amount ($)")
        expense_tree.heading("Notes", text="Notes")
        
        # Set column widths
        expense_tree.column("Date", width=120, anchor="center")
        expense_tree.column("Item", width=200)
        expense_tree.column("Category", width=150)
        expense_tree.column("Amount", width=100, anchor="e")
        expense_tree.column("Notes", width=300)
        
        expense_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Populate expense history
        def populate_expense_history():
            # Clear existing items
            for item in expense_tree.get_children():
                expense_tree.delete(item)
            
            # Get all expenses from items table (historical purchases)
            self.cursor.execute("""
                SELECT purchase_date, name, item_type, purchase_price, 'Purchase' 
                FROM items 
                WHERE purchase_price > 0
                ORDER BY purchase_date DESC
            """)
            
            for row in self.cursor.fetchall():
                date, item, category, amount, notes = row
                expense_tree.insert("", tk.END, values=(
                    date, item, category, f"{amount:.2f}", notes
                ))
        
        populate_expense_history()
        
        # Filter controls
        filter_frame = tk.Frame(history_frame, bg="#f5f7fa")
        filter_frame.pack(fill="x", pady=5)
        
        tk.Label(filter_frame, text="Filter by:", bg="#f5f7fa").pack(side="left", padx=5)
        
        # Year filter
        self.cursor.execute("SELECT DISTINCT strftime('%Y', purchase_date) FROM items ORDER BY purchase_date DESC")
        years = [row[0] for row in self.cursor.fetchall()]
        year_var = tk.StringVar()
        year_combo = ttk.Combobox(filter_frame, textvariable=year_var, values=years, width=8)
        year_combo.pack(side="left", padx=5)
        year_combo.set("All")
        
        # Month filter
        month_var = tk.StringVar()
        month_combo = ttk.Combobox(filter_frame, textvariable=month_var, 
                                values=["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], width=8)
        month_combo.pack(side="left", padx=5)
        month_combo.set("All")
        
        # Category filter
        self.cursor.execute("SELECT DISTINCT item_type FROM items")
        categories = [row[0] for row in self.cursor.fetchall()]
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(filter_frame, textvariable=category_var, 
                                    values=["All"] + categories, width=15)
        category_combo.pack(side="left", padx=5)
        category_combo.set("All")
        
        def apply_filters():
            year = year_var.get()
            month = month_var.get()
            category = category_var.get()
            
            query = """
                SELECT purchase_date, name, item_type, purchase_price, 'Purchase' 
                FROM items 
                WHERE purchase_price > 0
            """
            params = []
            
            conditions = []
            if year != "All":
                conditions.append("strftime('%Y', purchase_date) = ?")
                params.append(year)
            if month != "All":
                month_num = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(month) + 1
                conditions.append("strftime('%m', purchase_date) = ?")
                params.append(f"{month_num:02d}")
            if category != "All":
                conditions.append("item_type = ?")
                params.append(category)
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            query += " ORDER BY purchase_date DESC"
            
            self.cursor.execute(query, params)
            
            # Clear and repopulate tree
            for item in expense_tree.get_children():
                expense_tree.delete(item)
                
            for row in self.cursor.fetchall():
                date, item, category, amount, notes = row
                expense_tree.insert("", tk.END, values=(
                    date, item, category, f"{amount:.2f}", notes
                ))
        
        ttk.Button(filter_frame, text="Apply Filters", command=apply_filters).pack(side="left", padx=10)
        
        # Export button
        def export_expenses():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )
            if file_path:
                try:
                    self.cursor.execute("""
                        SELECT purchase_date, name, item_type, purchase_price, 'Purchase' 
                        FROM items 
                        WHERE purchase_price > 0
                        ORDER BY purchase_date DESC
                    """)
                    
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Date', 'Item', 'Category', 'Amount', 'Notes'])
                        writer.writerows(self.cursor.fetchall())
                    
                    messagebox.showinfo("Success", f"Expenses exported to {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export: {str(e)}")
        
        ttk.Button(history_frame, text="Export to CSV", command=export_expenses).pack(pady=10)
                
    def save_expense(self, item, category, amount, date, payment, notes):
        # Implementation as shown above
        pass

    def add_item(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Item")
        add_window.geometry("500x600")  # Increased size to accommodate new widgets
        add_window.config(bg="#FFFFFF")

        # Updated type options
        type_groups = {
            'Top Wear': ['Shirt', 'T-shirt', 'Kurti', 'Kurta'],
            'Bottom Wear': ['Pant', 'Trouser', 'Skirt', 'Leggings'],
            'Footwear': ['Shoes', 'Slipper', 'Sandals']
        }

        # Category selection
        tk.Label(add_window, text="Category:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        category = ttk.Combobox(add_window, values=list(type_groups.keys()), font=self.label_font)
        category.pack(pady=5)
        category.current(0)

        # Specific type selection
        tk.Label(add_window, text="Specific Type:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        type_combo = ttk.Combobox(add_window, font=self.label_font)
        type_combo.pack(pady=5)

        # Update specific types based on selected category
        def update_types(event=None):
            selected_category = category.get()
            type_combo['values'] = type_groups[selected_category]
            type_combo.current(0)

        category.bind("<<ComboboxSelected>>", update_types)
        update_types()  # Initialize the types

        # Name
        tk.Label(add_window, text="Enter Name:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        name_entry = tk.Entry(add_window, font=self.label_font)
        name_entry.pack(pady=5)

        # Purchase Price
        tk.Label(add_window, text="Purchase Price ($):", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        price_entry = tk.Entry(add_window, font=self.label_font)
        price_entry.pack(pady=5)
        price_entry.insert(0, "0.00")

        # Purchase Date with calendar picker
        tk.Label(add_window, text="Purchase Date:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        
        date_frame = tk.Frame(add_window, bg="#FFFFFF")
        date_frame.pack(pady=5)
        
        date_entry = tk.Entry(date_frame, font=self.label_font, width=12)
        date_entry.pack(side=tk.LEFT, padx=5)
        date_entry.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        
        def pick_date():
            date_window = tk.Toplevel(add_window)
            date_window.title("Select Date")
            date_window.geometry("300x300")
            
            cal = Calendar(date_window, selectmode='day', 
                        year=datetime.datetime.now().year, 
                        month=datetime.datetime.now().month, 
                        day=datetime.datetime.now().day)
            cal.pack(pady=20)
            
            def set_date():
                date_entry.delete(0, tk.END)
                date_entry.insert(0, cal.get_date())
                date_window.destroy()
                
            tk.Button(date_window, text="Select", command=set_date).pack(pady=10)
        
        date_btn = tk.Button(date_frame, text="📅", command=pick_date, 
                            font=("Arial", 12), bd=1, relief=tk.RAISED)
        date_btn.pack(side=tk.LEFT)

        # Color
        tk.Label(add_window, text="Select Color:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        colors = ["Red", "Blue", "Green", "Yellow", "Black", "White", "Pink", "Gray", "Orange", "Brown", "Purple", "Cyan"]
        color_select = ttk.Combobox(add_window, values=colors, font=self.label_font)
        color_select.pack(pady=5)
        color_select.current(0)

        # Fabric with better organization
        tk.Label(add_window, text="Select Fabric:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        
        # Organized fabric categories
        fabric_categories = {
            "Traditional Indian": ['Khadi', 'Chanderi', 'Tussar Silk', 'Eri Silk', 'Pashmina', 
                                'Mulmul', 'Banarasi Brocade', 'Kanjivaram Silk', 'Maheshwari',
                                'Kota Doria', 'Ikat', 'Bandhani', 'Ajrakh', 'Dhabu', 'Mashru'],
            "Western": ['Cotton', 'Silk', 'Linen', 'Wool', 'Denim', 'Hemp', 'Jute'],
            "Synthetic": ['Polyester', 'Nylon', 'Rayon (Viscose)', 'Acrylic', 'Lycra (Spandex)'],
            "Blends": ['Poly-Cotton', 'Silk-Cotton', 'Wool-Silk Blend', 'Rayon-Cotton Blend']
        }
        
        fabric_frame = tk.Frame(add_window, bg="#FFFFFF")
        fabric_frame.pack(pady=5)
        
        # Fabric type selection
        fabric_type = ttk.Combobox(fabric_frame, values=list(fabric_categories.keys()), 
                                font=self.label_font, state="readonly", width=15)
        fabric_type.pack(side=tk.LEFT, padx=5)
        fabric_type.current(0)
        
        # Specific fabric selection
        fabric_select = ttk.Combobox(fabric_frame, values=fabric_categories["Traditional Indian"], 
                                    font=self.label_font, width=20)
        fabric_select.pack(side=tk.LEFT, padx=5)
        fabric_select.current(0)
        
        def update_fabrics(event=None):
            selected_type = fabric_type.get()
            fabric_select['values'] = fabric_categories[selected_type]
            fabric_select.current(0)
        
        fabric_type.bind("<<ComboboxSelected>>", update_fabrics)

        def save_item():
            name = name_entry.get()
            item_type = type_combo.get()
            color = color_select.get()
            fabric = fabric_select.get()
            price = price_entry.get()
            purchase_date = date_entry.get()

            if not name:
                messagebox.showwarning("Warning", "Name cannot be empty.")
                return
            if not item_type:
                messagebox.showwarning("Warning", "Please select a specific type.")
                return

            try:
                price_float = float(price) if price else 0.0
                self.cursor.execute(
                    "INSERT INTO items (name, item_type, color, fabric, purchase_price, purchase_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, item_type, color, fabric, price_float, purchase_date))
                self.conn.commit()
                messagebox.showinfo("Success", f"{name} added successfully!")
                add_window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid price")
            except sqlite3.IntegrityError:
                messagebox.showwarning("Warning", 
                "An item with this combination (name + type + color + fabric) already exists.")

        save_button = tk.Button(
            add_window,
            text="Save Item",
            command=save_item,
            font=self.button_font,
            bg="#4CAF50",
            fg="white",
            bd=0,
            padx=20,
            pady=12
        )
        save_button.pack(pady=20)

    def show_items(self):
        """Show items without rating column"""
        items_window = tk.Toplevel(self.root)
        items_window.title("All Items")
        items_window.geometry("1100x600")
        items_window.config(bg="#FFFFFF")

        tree = ttk.Treeview(
            items_window, 
            columns=("ID", "Name", "Type", "Color", "Fabric", "Wear Count"), 
            show="headings"
        )
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("Type", text="Type")
        tree.heading("Color", text="Color")
        tree.heading("Fabric", text="Fabric")
        tree.heading("Wear Count", text="Wear Count")
        
        # Set column widths
        tree.column("ID", width=50, anchor=tk.CENTER)
        tree.column("Name", width=200)
        tree.column("Type", width=150)
        tree.column("Color", width=100)
        tree.column("Fabric", width=200)
        tree.column("Wear Count", width=100, anchor=tk.CENTER)
        
        tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self.cursor.execute("SELECT id, name, item_type, color, fabric, wear_count FROM items")
        for row in self.cursor.fetchall():
            tree.insert("", tk.END, values=row)

        def edit_item():
            selected = tree.focus()
            if selected:
                item_id = tree.item(selected)['values'][0]
                self.edit_item_window(item_id)
            else:
                messagebox.showwarning("Warning", "Select an item to edit.")

        def delete_item():
            selected = tree.focus()
            if selected:
                item_id = tree.item(selected)['values'][0]
                self.cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
                self.conn.commit()
                tree.delete(selected)
                messagebox.showinfo("Deleted", "Item deleted successfully!")
            else:
                messagebox.showwarning("Warning", "Select an item to delete.")

        edit_button = tk.Button(items_window, text="Edit Item", command=edit_item, 
                              font=self.button_font, bg="#2196F3", fg="white", bd=0)
        edit_button.pack(pady=10)
        delete_button = tk.Button(items_window, text="Delete Item", command=delete_item, 
                                font=self.button_font, bg="#F44336", fg="white", bd=0)
        delete_button.pack(pady=10)

    def edit_item_window(self, item_id):
        """Edit window with fabric selection"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Item")
        edit_window.geometry("400x400")
        edit_window.config(bg="#FFFFFF")

        self.cursor.execute("SELECT * FROM items WHERE id=?", (item_id,))
        item = self.cursor.fetchone()

        # Type
        tk.Label(edit_window, text="Select Type:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        item_type = ttk.Combobox(edit_window, values=["Shirt", "Pant", "Shoes"], font=self.label_font)
        item_type.pack(pady=5)
        item_type.set(item[2])

        # Name
        tk.Label(edit_window, text="Enter Name:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        name_entry = tk.Entry(edit_window, font=self.label_font)
        name_entry.pack(pady=5)
        name_entry.insert(0, item[1])

        # Color
        tk.Label(edit_window, text="Select Color:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        colors = ["Red", "Blue", "Green", "Yellow", "Black", "White", "Pink", "Gray", "Orange", "Brown", "Purple", "Cyan"]
        color_select = ttk.Combobox(edit_window, values=colors, font=self.label_font)
        color_select.pack(pady=5)
        color_select.set(item[3])

        # Fabric
        tk.Label(edit_window, text="Select Fabric:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        fabrics = [
            'Cotton', 'Silk', 'Linen', 'Wool', 'Jute', 'Hemp', 'Khadi',
            'Chanderi', 'Tussar Silk', 'Eri Silk', 'Pashmina', 'Mulmul',
            'Banarasi Brocade', 'Kanjivaram Silk', 'Maheshwari', 'Polyester',
            'Nylon', 'Rayon (Viscose)', 'Acrylic', 'Lycra (Spandex)',
            'Poly-Cotton', 'Silk-Cotton', 'Wool-Silk Blend', 'Rayon-Cotton Blend',
            'Kota Doria', 'Ikat', 'Bandhani', 'Ajrakh', 'Dhabu', 'Mashru'
        ]
        fabric_select = ttk.Combobox(edit_window, values=fabrics, font=self.label_font)
        fabric_select.pack(pady=5)
        fabric_select.set(item[4])

        # Purchase Price
        tk.Label(edit_window, text="Purchase Price ($):", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        price_entry = tk.Entry(edit_window, font=self.label_font)
        price_entry.pack(pady=5)
        price_entry.insert(0, item[6] if item[6] else "0.00")

        # Purchase Date
        tk.Label(edit_window, text="Purchase Date (YYYY-MM-DD):", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        date_entry = tk.Entry(edit_window, font=self.label_font)
        date_entry.pack(pady=5)
        date_entry.insert(0, item[7] if item[7] else datetime.date.today().strftime("%Y-%m-%d"))

        def save_edited_item():
            name = name_entry.get()
            item_type_val = item_type.get()
            color = color_select.get()
            fabric = fabric_select.get()
            price = price_entry.get()
            purchase_date = date_entry.get()

            if name:
                try:
                    price_float = float(price) if price else 0.0
                    self.cursor.execute(
                        "UPDATE items SET name=?, item_type=?, color=?, fabric=?, purchase_price=?, purchase_date=? WHERE id=?", 
                        (name, item_type_val, color, fabric, price_float, purchase_date, item_id))
                    self.conn.commit()
                    messagebox.showinfo("Success", f"{name} updated successfully!")
                    edit_window.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid price")
            else:
                messagebox.showwarning("Warning", "Name cannot be empty.")
        
        save_button = tk.Button(
            edit_window,
            text="Save Changes",
            command=save_edited_item,
            font=self.button_font,
            bg="#4CAF50",
            fg="white",
            bd=0,
            padx=15,
            pady=10
        )
        save_button.pack(pady=20)

    def schedulize(self):
        """Generate a 7-day schedule using advanced fashion algorithms"""
        try:
            print("Fetching items from the database...")
            self.cursor.execute("SELECT id, name, item_type, color, fabric, wear_count FROM items")
            items = [self.Item(*row) for row in self.cursor.fetchall()]
            print(f"Found {len(items)} items in the database")

            # Minimum requirements check
            tops = [item for item in items if item.item_type.lower() in ['shirt', 't-shirt', 'top', 'kurti', 'kurta']]
            bottoms = [item for item in items if item.item_type.lower() in ['pant', 'trouser', 'bottom', 'skirt', 'leggings']]
            footwear = [item for item in items if item.item_type.lower() in ['shoes', 'footwear', 'slipper', 'sandals']]

            if len(tops) < 7 or len(bottoms) < 7 or len(footwear) < 7:
                message = "You need at least:\n"
                message += f"- {max(0, 7-len(tops))} more top wear items\n" if len(tops) < 7 else ""
                message += f"- {max(0, 7-len(bottoms))} more bottom wear items\n" if len(bottoms) < 7 else ""
                message += f"- {max(0, 7-len(footwear))} more footwear items" if len(footwear) < 7 else ""
                messagebox.showwarning("Insufficient Items", message)
                return

            class FashionAlgorithm:
                def __init__(self, tops, bottoms, footwear):
                    self.tops = tops
                    self.bottoms = bottoms
                    self.footwear = footwear
                    self.color_rules = self.load_color_rules()
                    self.fabric_rules = self.load_fabric_rules()
                    self.occasion_rules = self.load_occasion_rules()
                    self.trend_data = self.load_trend_data()

                def load_color_rules(self):
                    return {
                        'analogous': {'weight': 0.4, 'angle_range': 30},
                        'complementary': {'weight': 0.3, 'angle_diff': 180},
                        'triadic': {'weight': 0.2, 'angle_diff': 120},
                        'monochromatic': {'weight': 0.1, 'threshold': 0.1}
                    }
                
                def load_fabric_rules(self):
                    return {
                        'formal': ['silk', 'wool', 'linen', 'cotton'],
                        'casual': ['denim', 'cotton', 'jersey', 'knit'],
                        'summer': ['linen', 'cotton', 'chiffon'],
                        'winter': ['wool', 'cashmere', 'tweed']
                    }
                
                def load_occasion_rules(self):
                    return {
                        'work': {'formality': 0.8, 'color_variety': 0.3},
                        'casual': {'formality': 0.3, 'color_variety': 0.7},
                        'evening': {'formality': 0.9, 'color_variety': 0.5}
                    }
                
                def load_trend_data(self):
                    return {
                        'colors': ['sage green', 'cream white', 'deep navy', 'rust'],
                        'fabrics': ['organic cotton', 'linen', 'recycled polyester'],
                        'styles': ['oversized', 'minimalist', 'vintage']
                    }
                
                def color_to_hsv(self, color_name):
                    color_map = {
                        'red': (0, 1, 1), 'orange': (30, 1, 1), 'yellow': (60, 1, 1),
                        'green': (120, 1, 1), 'blue': (240, 1, 1), 'purple': (270, 1, 1),
                        'pink': (330, 1, 1), 'brown': (20, 0.5, 0.5), 'black': (0, 0, 0),
                        'white': (0, 0, 1), 'gray': (0, 0, 0.5), 'navy': (240, 1, 0.5),
                        'sage green': (100, 0.5, 0.7), 'cream white': (60, 0.1, 1),
                        'deep navy': (240, 1, 0.4), 'rust': (20, 0.8, 0.6)
                    }
                    return color_map.get(color_name.lower(), (0, 0, 0.5))
                
                def color_harmony_score(self, color1, color2):
                    try:
                        h1, s1, v1 = self.color_to_hsv(color1)
                        h2, s2, v2 = self.color_to_hsv(color2)
                        hue_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
                        
                        scores = []
                        for rule, params in self.color_rules.items():
                            if rule == 'analogous' and hue_diff <= params['angle_range']:
                                scores.append(params['weight'])
                            elif rule == 'complementary' and abs(hue_diff - params['angle_diff']) <= 15:
                                scores.append(params['weight'])
                            elif rule == 'triadic' and (abs(hue_diff - params['angle_diff']) <= 15 or 
                                                    abs(hue_diff - params['angle_diff']*2) <= 15):
                                scores.append(params['weight'])
                            elif rule == 'monochromatic' and hue_diff <= params['threshold']*360:
                                scores.append(params['weight'])
                        
                        return max(scores) if scores else 0.1
                    except:
                        return 0.3
                
                def fabric_compatibility(self, top_fabric, bottom_fabric):
                    for category, fabrics in self.fabric_rules.items():
                        if top_fabric.lower() in fabrics and bottom_fabric.lower() in fabrics:
                            return 0.8
                    return 0.3
                
                def trend_score(self, item):
                    score = 0
                    if any(trend_color in item.color.lower() for trend_color in self.trend_data['colors']):
                        score += 0.4
                    if any(trend_fabric in item.fabric.lower() for trend_fabric in self.trend_data['fabrics']):
                        score += 0.3
                    return score
                
                def occasion_suitability(self, top, bottom, shoes, day_index):
                    occasions = {0: 'work', 1: 'work', 2: 'work', 3: 'work', 
                                4: 'casual', 5: 'casual', 6: 'evening'}
                    occasion = occasions.get(day_index, 'casual')
                    rules = self.occasion_rules.get(occasion, {})
                    
                    formality_score = 0
                    formality_score += 0.4 if top.item_type.lower() in ['shirt', 'kurta'] else 0
                    formality_score += 0.3 if bottom.item_type.lower() in ['pant', 'trouser'] else 0
                    formality_score += 0.3 if shoes.item_type.lower() == 'shoes' else 0
                    
                    color_variety = 1 if top.color.lower() != bottom.color.lower() else 0
                    
                    formality_diff = abs(formality_score - rules.get('formality', 0.5))
                    color_diff = abs(color_variety - rules.get('color_variety', 0.5))
                    
                    return 1 - (formality_diff + color_diff)/2
                
                def calculate_outfit_score(self, top, bottom, shoes, day_index):
                    color_score = (self.color_harmony_score(top.color, bottom.color) * 0.6 +
                                self.color_harmony_score(top.color, shoes.color) * 0.4)
                    fabric_score = self.fabric_compatibility(top.fabric, bottom.fabric)
                    trend_score = (self.trend_score(top) + self.trend_score(bottom) + 
                                self.trend_score(shoes)) / 3
                    occasion_score = self.occasion_suitability(top, bottom, shoes, day_index)
                    wear_score = 1 - (top.wear_count + bottom.wear_count + shoes.wear_count) / (3 * 10)
                    
                    return (color_score * 0.3 + fabric_score * 0.2 + trend_score * 0.15 +
                        occasion_score * 0.15 + wear_score * 0.1)
                
                def generate_outfits(self, days=7):
                    outfits = []
                    used_items = set()
                    
                    for day in range(days):
                        best_score = -1
                        best_outfit = None
                        
                        for _ in range(100):  # Limit iterations
                            available_tops = [t for t in self.tops if t.id not in used_items]
                            available_bottoms = [b for b in self.bottoms if b.id not in used_items]
                            available_footwear = [f for f in self.footwear if f.id not in used_items]
                            
                            if not available_tops or not available_bottoms or not available_footwear:
                                break
                            
                            top = random.choice(available_tops)
                            bottom = random.choice(available_bottoms)
                            shoe = random.choice(available_footwear)
                            
                            score = self.calculate_outfit_score(top, bottom, shoe, day)
                            
                            if self.color_harmony_score(top.color, bottom.color) > 0.7:
                                score *= 1.2
                            
                            if score > best_score:
                                best_score = score
                                best_outfit = (top, bottom, shoe)
                        
                        if best_outfit:
                            top, bottom, shoe = best_outfit
                            outfits.append((day, best_outfit))
                            used_items.update({top.id, bottom.id, shoe.id})
                    
                    return outfits

            # Initialize and run fashion algorithm
            fashion_algo = FashionAlgorithm(tops, bottoms, footwear)
            outfits = fashion_algo.generate_outfits(days=7)
            
            if len(outfits) < 7:
                missing_days = 7 - len(outfits)
                message = f"Generated only {len(outfits)} outfits. Need {missing_days} more.\n"
                message += "Consider adding more items or relaxing fashion constraints."
                messagebox.showwarning("Partial Schedule", message)
            
            # Save to database
            self.cursor.execute("DELETE FROM schedule")
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day_idx, (top, bottom, shoe) in outfits:
                self.cursor.execute(
                    "INSERT INTO schedule (day, shirt, pant, shoes) VALUES (?, ?, ?, ?)",
                    (day_names[day_idx], top.name, bottom.name, shoe.name)
                )
            
            self.conn.commit()
            messagebox.showinfo("Success", "7-day schedule generated successfully!")

        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to generate schedule: {e}")
            
    # Define Item class (needed for row conversion)
    class Item:
        def __init__(self, id, name, item_type, color, fabric, wear_count):
            self.id = id
            self.name = name
            self.item_type = item_type
            self.color = color
            self.fabric = fabric
            self.wear_count = wear_count

    def open_schedule_page(self):
        schedule_window = tk.Toplevel(self.root)
        schedule_window.title("Weekly Wardrobe Schedule")
        schedule_window.geometry("1100x650")
        
        # Store references for this window
        schedule_window.tree = None
        schedule_window.week_label = None
        schedule_window.current_week_dates = None
        
        # Add date navigation controls
        nav_frame = tk.Frame(schedule_window)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Get current week's dates
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        schedule_window.current_week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
        
        # Navigation buttons with proper command binding
        prev_week_btn = tk.Button(nav_frame, text="◀ Previous Week", 
                                command=lambda: self.change_week(schedule_window, -7))
        prev_week_btn.pack(side=tk.LEFT)
        
        next_week_btn = tk.Button(nav_frame, text="Next Week ▶", 
                                command=lambda: self.change_week(schedule_window, 7))
        next_week_btn.pack(side=tk.LEFT)
        
        today_btn = tk.Button(nav_frame, text="Today", 
                            command=lambda: self.change_week(schedule_window, 0))
        today_btn.pack(side=tk.LEFT, padx=10)
        
        # Week label
        week_label = tk.Label(nav_frame, 
                            text=f"Week of {start_of_week.strftime('%b %d, %Y')}",
                            font=("Arial", 12, "bold"))
        week_label.pack(side=tk.LEFT, padx=20)
        schedule_window.week_label = week_label
        
        # Main schedule treeview
        tree = ttk.Treeview(
            schedule_window,
            columns=("Day", "Date", "Top Wear", "Bottom Wear", "Footwear"),
            show="headings",
            height=7
        )
        tree.heading("Day", text="Day", anchor=tk.CENTER)
        tree.heading("Date", text="Date", anchor=tk.CENTER)
        tree.heading("Top Wear", text="Top Wear (Color)", anchor=tk.CENTER)
        tree.heading("Bottom Wear", text="Bottom Wear (Color)", anchor=tk.CENTER)
        tree.heading("Footwear", text="Footwear (Color)", anchor=tk.CENTER)

        # Set column widths
        tree.column("Day", width=120, anchor=tk.CENTER)
        tree.column("Date", width=120, anchor=tk.CENTER)
        tree.column("Top Wear", width=220, anchor=tk.CENTER)
        tree.column("Bottom Wear", width=220, anchor=tk.CENTER)
        tree.column("Footwear", width=220, anchor=tk.CENTER)

        # Pack the Treeview
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        schedule_window.tree = tree
        
        # Load schedule data
        self.load_schedule_data(schedule_window)
        
        # Add action buttons
        button_frame = tk.Frame(schedule_window)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Preview Colors button
        preview_button = tk.Button(
            button_frame,
            text="Preview Colors",
            command=lambda: self.show_color_preview(schedule_window),
            font=self.button_font,
            bg="#4CAF50",
            fg="white"
        )
        preview_button.pack(side=tk.LEFT, padx=20)
        
        # Rate button
        rate_btn = tk.Button(
            button_frame,
            text="Rate Outfit",
            command=lambda: self.rate_selected_outfit(schedule_window),
            font=self.button_font,
            bg="#FFA500",
            fg="white"
        )
        rate_btn.pack(side=tk.LEFT, padx=20)
        
        # Clear button
        clear_btn = tk.Button(
            button_frame,
            text="Clear Schedule",
            command=self.clear_schedule,
            font=self.button_font,
            bg="#FF4444",
            fg="white"
        )
        clear_btn.pack(side=tk.RIGHT, padx=20)
        
        # Close window callback
        schedule_window.protocol("WM_DELETE_WINDOW", lambda: self.on_schedule_close(schedule_window))

    def on_schedule_close(self, window):
        """Clean up when schedule window is closed"""
        if hasattr(window, 'tree'):
            del window.tree
        if hasattr(window, 'week_label'):
            del window.week_label
        if hasattr(window, 'current_week_dates'):
            del window.current_week_dates
        window.destroy()    

    def change_week(self, window, days):
        """Change the current week view by the specified number of days"""
        if not hasattr(window, 'current_week_dates'):
            return
            
        if days == 0:  # Today button
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            window.current_week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
        else:
            # Move all dates by the specified number of days
            window.current_week_dates = [d + timedelta(days=days) for d in window.current_week_dates]
        
        # Update the week label
        if hasattr(window, 'week_label'):
            window.week_label.config(text=f"Week of {window.current_week_dates[0].strftime('%b %d, %Y')}")
        
        # Reload schedule data
        self.load_schedule_data(window)

    def load_schedule_data(self, window):
        """Load schedule data into the treeview for this window"""
        if not hasattr(window, 'tree') or not hasattr(window, 'current_week_dates'):
            return
        
        tree = window.tree
        
        # Clear existing data
        for item in tree.get_children():
            tree.delete(item)
        
        # Day names for reference
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for i, day_date in enumerate(window.current_week_dates):
            day_name = day_names[i]
            date_str = day_date.strftime("%Y-%m-%d")
            
            # First check specific date schedule
            self.cursor.execute('''
                SELECT s.day, i1.name, i2.name, i3.name
                FROM schedule s
                LEFT JOIN items i1 ON s.shirt = i1.name
                LEFT JOIN items i2 ON s.pant = i2.name
                LEFT JOIN items i3 ON s.shoes = i3.name
                WHERE s.day = ?
            ''', (date_str,))
            outfit = self.cursor.fetchone()
            
            # If no specific date, check weekly schedule
            if not outfit:
                self.cursor.execute('''
                    SELECT s.day, i1.name, i2.name, i3.name
                    FROM schedule s
                    LEFT JOIN items i1 ON s.shirt = i1.name
                    LEFT JOIN items i2 ON s.pant = i2.name
                    LEFT JOIN items i3 ON s.shoes = i3.name
                    WHERE s.day = ?
                ''', (day_name,))
                outfit = self.cursor.fetchone()
            
            # Prepare values for treeview
            if outfit:
                day, top, bottom, shoes = outfit
                values = (
                    day_name,
                    day_date.strftime("%b %d"),
                    f"{top} ({self.get_item_color(top)})" if top else "None",
                    f"{bottom} ({self.get_item_color(bottom)})" if bottom else "None",
                    f"{shoes} ({self.get_item_color(shoes)})" if shoes else "None"
                )
            else:
                values = (
                    day_name,
                    day_date.strftime("%b %d"),
                    "None",
                    "None",
                    "None"
                )
            
            # Insert into treeview
            item_id = tree.insert("", tk.END, values=values)
            
            # Highlight today's date
            if day_date == date.today():
                tree.tag_configure('today', background='#E3F2FD')
                tree.item(item_id, tags=('today',))

    def get_item_color(self, item_name):
        """Get color for an item by name"""
        if not item_name or item_name == "None":
            return "None"
        
        self.cursor.execute("SELECT color FROM items WHERE name=?", (item_name,))
        result = self.cursor.fetchone()
        return result[0] if result else "None"

    def clear_schedule(self):
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to clear the schedule?")
        if confirm:
            self.cursor.execute("DELETE FROM schedule")
            self.conn.commit()
            messagebox.showinfo("Success", "Schedule cleared successfully!")

    def rate_outfit_window(self, shirt, pant, shoes):
        """Rate the entire outfit with a single rating"""
        rate_window = tk.Toplevel(self.root)
        rate_window.title("Rate Outfit")
        rate_window.geometry("300x200")
        rate_window.config(bg="#FFFFFF")

        tk.Label(rate_window, text="Rate the entire outfit (1-5):", 
                 font=self.label_font, bg="#FFFFFF").pack(pady=15)
        
        rating_var = tk.IntVar(value=3)
        ttk.Combobox(rate_window, textvariable=rating_var, 
                     values=[1, 2, 3, 4, 5], state="readonly").pack(pady=10)

        def save_rating():
            rating = rating_var.get()
            # Save to outfit_ratings table
            try:
                # Create table if not exists
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS outfit_ratings (
                        id INTEGER PRIMARY KEY,
                        shirt TEXT NOT NULL,
                        pant TEXT NOT NULL,
                        shoes TEXT NOT NULL,
                        rating INTEGER NOT NULL,
                        UNIQUE(shirt, pant, shoes)
                    )
                ''')
                
                # Check if rating exists for this outfit
                self.cursor.execute(
                    "SELECT 1 FROM outfit_ratings WHERE shirt=? AND pant=? AND shoes=?",
                    (shirt, pant, shoes))
                exists = self.cursor.fetchone()
                
                if exists:
                    # Update existing rating
                    self.cursor.execute(
                        "UPDATE outfit_ratings SET rating=? WHERE shirt=? AND pant=? AND shoes=?",
                        (rating, shirt, pant, shoes))
                else:
                    # Insert new rating
                    self.cursor.execute(
                        "INSERT INTO outfit_ratings (shirt, pant, shoes, rating) VALUES (?, ?, ?, ?)",
                        (shirt, pant, shoes, rating))
                
                self.conn.commit()
                messagebox.showinfo("Success", f"Outfit rating saved: {rating} stars")
                rate_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save rating: {str(e)}")

        tk.Button(
            rate_window,
            text="Save Rating",
            command=save_rating,
            font=self.button_font,
            bg="#4CAF50",
            fg="white"
        ).pack(pady=20)

    def backup_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "w") as file:
                self.cursor.execute("SELECT * FROM items")
                for row in self.cursor.fetchall():
                    file.write(f"{row}\n")
            messagebox.showinfo("Success", f"Data exported to {file_path}")

    def search_items(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("Search Items")
        search_window.geometry("400x200")
        search_window.config(bg="#FFFFFF")

        tk.Label(search_window, text="Search by:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        search_type = ttk.Combobox(search_window, values=["Name", "Type", "Color"], font=self.label_font)
        search_type.pack(pady=5)
        search_type.current(0)

        tk.Label(search_window, text="Enter search term:", font=self.label_font, bg="#FFFFFF", fg="#333333").pack(pady=5)
        search_entry = tk.Entry(search_window, font=self.label_font)
        search_entry.pack(pady=5)

        def perform_search():
            search_term = search_entry.get()
            search_by = search_type.get().lower()
            allowed_columns = {'name', 'item_type', 'color'}
            if search_by not in allowed_columns:
                messagebox.showwarning("Warning", "Invalid search type.")
                return
            self.cursor.execute(f"SELECT * FROM items WHERE {search_by} LIKE ?", (f"%{search_term}%",))
            results = self.cursor.fetchall()
            if results:
                self.show_search_results(results)
            else:
                messagebox.showinfo("No Results", "No items found matching your search.")

        search_button = tk.Button(search_window, text="Search", command=perform_search, font=self.button_font, bg="#00BCD4", fg="white", bd=0)
        search_button.pack(pady=10)

    def show_search_results(self, results):
        results_window = tk.Toplevel(self.root)
        results_window.title("Search Results")
        results_window.geometry("1200x600")
        results_window.config(bg="#FFFFFF")

        tree = ttk.Treeview(
            results_window, 
            columns=("ID", "Name", "Type", "Color", "Fabric", "Wear Count"), 
            show="headings"
        )
        
        # Correct column configuration
        columns = [
            ("ID", 50), ("Name", 200), ("Type", 150), 
            ("Color", 100), ("Fabric", 200), ("Wear Count", 100)
        ]
        
        for col, width in columns:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=tk.CENTER)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        for row in results:
            tree.insert("", tk.END, values=row)

    def open_dashboard(self):
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("Wardrobe Analytics Dashboard")
        dashboard_window.geometry("1400x800")
        dashboard_window.config(bg="#FFFFFF")

        # Main container
        main_frame = tk.Frame(dashboard_window, bg="#FFFFFF")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)

        # Category statistics
        categories = {
            "Top Wear": ['Shirt', 'T-shirt', 'Kurti', 'Kurta'],
            "Bottom Wear": ['Pant', 'Trouser', 'Skirt', 'Leggings'],
            "Footwear": ['Shoes', 'Slipper', 'Sandals']
        }

        # Create category frames
        for idx, (category, types) in enumerate(categories.items()):
            frame = tk.Frame(main_frame, bg="#F8F9FA", bd=2, relief=tk.GROOVE)
            frame.grid(row=0, column=idx, padx=20, pady=20, sticky="nsew")
            
            # Category header
            tk.Label(frame, text=category, 
                    font=("Segoe UI", 14, "bold"), 
                    bg="#F8F9FA", fg="#2C3E50").pack(pady=10)
            
            # Get total items in category
            self.cursor.execute(f'''
                SELECT COUNT(*) FROM items 
                WHERE item_type IN ({','.join(['?']*len(types))})
            ''', types)
            total = self.cursor.fetchone()[0]
            tk.Label(frame, text=f"Total Items: {total}", 
                    font=("Segoe UI", 12), bg="#F8F9FA").pack()
            
            # Type breakdown
            type_frame = tk.Frame(frame, bg="#F8F9FA")
            type_frame.pack(pady=10)
            
            for t_idx, item_type in enumerate(types):
                self.cursor.execute("SELECT COUNT(*) FROM items WHERE item_type=?", (item_type,))
                count = self.cursor.fetchone()[0]
                
                tk.Label(type_frame, text=f"{item_type}: {count}", 
                        font=("Segoe UI", 10), bg="#F8F9FA", 
                        anchor="w").grid(row=t_idx, column=0, sticky="w", padx=10)

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)

        # Add other statistics below
        stats_frame = tk.Frame(main_frame, bg="#FFFFFF")
        stats_frame.grid(row=1, column=0, columnspan=3, pady=40)

        # Most Worn Item
        self.cursor.execute('''
            SELECT name, wear_count FROM items 
            ORDER BY wear_count DESC LIMIT 1
        ''')
        most_worn = self.cursor.fetchone()
        if most_worn:
            tk.Label(stats_frame, text=f"🌟 Most Worn: {most_worn[0]} ({most_worn[1]} wears)",
                    font=("Segoe UI", 12), bg="#FFFFFF").pack(side=tk.LEFT, padx=20)
            
    def weather_suggestions(self):
        def get_user_location():
            """Prompt user for their city."""
            location_window = tk.Toplevel(self.root)
            location_window.title("Enter Your City")
            location_window.geometry("300x150")
            location_window.config(bg="#FFFFFF")

            tk.Label(location_window, text="Enter your city:", font=self.label_font, bg="#FFFFFF").pack(pady=10)
            city_entry = tk.Entry(location_window, font=self.label_font)
            city_entry.pack(pady=10)

            def submit_city():
                city = city_entry.get()
                if city:
                    location_window.city = city
                    location_window.destroy()
                else:
                    messagebox.showwarning("Warning", "City name cannot be empty.")

            submit_button = tk.Button(location_window, text="Submit", command=submit_city,
                                    font=self.button_font, bg="#4CAF50", fg="white")
            submit_button.pack(pady=10)

            location_window.wait_window()
            return getattr(location_window, 'city', None)

        city = get_user_location()
        if not city:
            return

        # Use OpenWeatherMap API
        api_key = "ed3fd15a9b81d0193b1722f486de6243"  # Replace with your actual API key
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()

            # Check if the API returned valid data
            if data.get("cod") != 200:
                error_message = data.get("message", "Unknown error")
                messagebox.showerror("Error", f"Failed to fetch weather data: {error_message}")
                return

            # Extract weather data
            weather_main = data['weather'][0]['main']
            weather_description = data['weather'][0]['description']
            temperature_kelvin = data['main']['temp']
            temperature_celsius = round(temperature_kelvin - 273.15, 1)  # Convert to Celsius
            temperature_fahrenheit = round((temperature_kelvin - 273.15) * 9/5 + 32, 1)  # Convert to Fahrenheit
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            cloudiness = data['clouds']['all']

            # Generate outfit suggestions based on weather conditions
            suggestion = self.generate_outfit_suggestion(
                temperature_celsius, weather_main, weather_description, humidity, wind_speed, cloudiness
            )

            # Display weather and suggestion
            message = (
                f"Weather in {city}:\n"
                f"Condition: {weather_main} ({weather_description})\n"
                f"Temperature: {temperature_celsius}°C / {temperature_fahrenheit}°F\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind_speed} m/s\n"
                f"Cloudiness: {cloudiness}%\n\n"
                f"Suggestion: {suggestion}"
            )

            messagebox.showinfo("Weather Suggestion", message)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch weather data: {e}")
        except KeyError as e:
            messagebox.showerror("Error", f"Invalid data received from the API: {e}")

    def generate_outfit_suggestion(self, temperature, weather_main, weather_description, humidity, wind_speed, cloudiness):
        suggestion = []

        # Temperature-based suggestions
        if temperature < 0:
            suggestion.append("It's freezing! Wear a heavy winter coat, thermal layers, gloves, and a scarf.")
        elif temperature < 10:
            suggestion.append("It's cold! Wear a heavy jacket, sweater, and boots.")
        elif temperature < 20:
            suggestion.append("It's cool. Wear a light jacket, long-sleeve shirt, and jeans.")
        elif temperature < 30:
            suggestion.append("It's warm. Wear a t-shirt, shorts, and sneakers.")
        else:
            suggestion.append("It's hot! Wear light, breathable fabrics like cotton or linen.")

        # Weather condition-based suggestions
        if "rain" in weather_description.lower():
            suggestion.append("Don't forget to carry an umbrella or wear waterproof shoes.")
        if "snow" in weather_description.lower():
            suggestion.append("Wear insulated boots and a waterproof jacket.")
        if "clear" in weather_description.lower() and cloudiness < 20:
            suggestion.append("It's sunny! Wear sunglasses and apply sunscreen.")
        if wind_speed > 10:
            suggestion.append("It's windy! Wear a windbreaker or scarf to protect yourself.")

        # Humidity-based suggestions
        if humidity > 70:
            suggestion.append("It's humid. Wear moisture-wicking fabrics to stay comfortable.")
        elif humidity < 30:
            suggestion.append("It's dry. Stay hydrated and consider using moisturizer.")

        # Combine all suggestions into a single string
        return "\n".join(suggestion)
    
    color_map = {
            "navy": "#001f3f", "blue": "#0074D9", "black": "#000000",
            "white": "#FFFFFF", "red": "#FF4136", "green": "#2ECC40",
            "yellow": "#FFDC00", "pink": "#F012BE", "gray": "#AAAAAA",
            "orange": "#FF851B", "brown": "#A52A2A", "purple": "#B10DC9",
            "cyan": "#7FDBFF", "sage green": "#9DC183", "cream white": "#FFFDD0",
            "nude": "#F3E5AB", "beige": "#F5F5DC", "maroon": "#800000",
            "teal": "#008080", "lavender": "#E6E6FA", "olive": "#808000",
            "mustard": "#FFDB58", "burgundy": "#800020", "coral": "#FF7F50",
            "indigo": "#4B0082", "turquoise": "#40E0D0", "gold": "#FFD700",
            "silver": "#C0C0C0"
        }

    def show_color_preview(self, window):
        """Show color preview for selected outfit"""
        if not hasattr(window, 'tree'):
            return
            
        tree = window.tree
        selected = tree.focus()
        if selected:
            values = tree.item(selected)['values']
            if len(values) == 5:  # Now we have 5 columns
                day, date_str, top, bottom, shoes = values
                
                # Extract colors from the item names
                top_color = self.extract_color(top)
                bottom_color = self.extract_color(bottom)
                shoes_color = self.extract_color(shoes)
                
                # Create the color palette visualization
                self.create_enhanced_palette(top_color, bottom_color, shoes_color, f"{day} - {date_str}")
        else:
            messagebox.showwarning("Warning", "Please select an outfit to preview colors.")

    def rate_selected_outfit(self, window):
        """Rate the selected outfit"""
        if not hasattr(window, 'tree'):
            return
            
        tree = window.tree
        selected = tree.focus()
        if selected:
            values = tree.item(selected)['values']
            if len(values) == 5:  # Now we have 5 columns
                day, date_str, top, bottom, shoes = values
                
                # Extract item names without color information
                top_name = top.split(' (')[0] if '(' in top else top
                bottom_name = bottom.split(' (')[0] if '(' in bottom else bottom
                shoes_name = shoes.split(' (')[0] if '(' in shoes else shoes
                
                # Only allow rating if all items are present
                if "None" not in (top_name, bottom_name, shoes_name):
                    self.rate_outfit_window(top_name, bottom_name, shoes_name)
                else:
                    messagebox.showwarning("Warning", "Complete outfit required for rating")
        else:
            messagebox.showwarning("Warning", "Please select an outfit to rate.")

    def extract_color(self, item_str):
        """Extract color from item string (handles 'None' case)"""
        if item_str == "None":
            return "None"
        if '(' in item_str and ')' in item_str:
            return item_str.split(' (')[1].rstrip(')')
        return "white"  # Default color           

    def create_enhanced_palette(self, top_color, bottom_color, shoes_color, day):
        """Create a properly fitted outfit visualization window"""
        palette_window = tk.Toplevel(self.root)
        palette_window.title(f"Outfit Visualizer - {day}")
        palette_window.geometry("1000x650")  # Optimized size for single page
        palette_window.resizable(False, False)  # Prevent resizing to maintain layout
        
        # Main container using grid layout
        main_frame = tk.Frame(palette_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(main_frame, text=f"{day}'s Outfit", 
                font=("Helvetica", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left panel - Mannequin (40%)
        left_frame = tk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        
        # Create and display compact mannequin
        mannequin_img = self.create_mannequin_image(
            self.get_hex_color(top_color),
            self.get_hex_color(bottom_color),
            self.get_hex_color(shoes_color)
        )
        mannequin_img = mannequin_img.resize((300, 500), Image.LANCZOS)  # Compact size
        mannequin_tk = ImageTk.PhotoImage(mannequin_img)
        
        mannequin_label = tk.Label(left_frame, image=mannequin_tk)
        mannequin_label.image = mannequin_tk
        mannequin_label.pack()

        # Right panel - Color info (60%)
        right_frame = tk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Color Harmony
        harmony_tab = ttk.Frame(notebook)
        notebook.add(harmony_tab, text="Color Harmony")
        
        # Color wheel
        wheel_frame = tk.Frame(harmony_tab, pady=10)
        wheel_frame.pack(fill=tk.BOTH, expand=True)
        
        wheel_canvas = tk.Canvas(wheel_frame, width=300, height=300)
        wheel_canvas.pack()
        self.draw_color_wheel(wheel_canvas, 
                            self.get_hex_color(top_color),
                            self.get_hex_color(bottom_color),
                            self.get_hex_color(shoes_color))
        
        # Tab 2: Color Details
        details_tab = ttk.Frame(notebook)
        notebook.add(details_tab, text="Color Details")
        
        # Create compact color details
        self.create_compact_color_details(details_tab, top_color, bottom_color, shoes_color)
        
        # Tab 3: Suggestions
        suggestions_tab = ttk.Frame(notebook)
        notebook.add(suggestions_tab, text="Suggestions")
        
        # Create harmony suggestions
        self.create_harmony_suggestions(suggestions_tab, 
                                    self.get_hex_color(top_color),
                                    self.get_hex_color(bottom_color),
                                    self.get_hex_color(shoes_color))
        
        # Close button
        close_btn = tk.Button(main_frame, text="Close", command=palette_window.destroy,
                            font=("Helvetica", 10), bg="#f44336", fg="white")
        close_btn.grid(row=2, column=0, columnspan=2, pady=20)

    def create_compact_color_details(self, parent, top_color, bottom_color, shoes_color):
        """Create compact color details layout"""
        # Main container
        detail_frame = tk.Frame(parent)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Grid layout for colors
        colors = [
            ("Top Wear", top_color),
            ("Bottom Wear", bottom_color),
            ("Footwear", shoes_color)
        ]
        
        for i, (label, color) in enumerate(colors):
            # Color frame
            color_frame = tk.Frame(detail_frame)
            color_frame.grid(row=i, column=0, sticky="w", pady=5)
            
            # Swatch
            tk.Frame(color_frame, width=25, height=25, bg=self.get_hex_color(color),
                    bd=1, relief=tk.SOLID).grid(row=0, column=0, padx=5)
            
            # Info labels
            tk.Label(color_frame, text=f"{label}: {color.title()}", 
                    font=("Helvetica", 10)).grid(row=0, column=1, sticky="w")
            tk.Label(color_frame, text=f"HEX: {self.get_hex_color(color)}", 
                    font=("Helvetica", 9), fg="#666").grid(row=1, column=1, sticky="w")
        
        # Add color harmony explanation
        harmony_frame = tk.Frame(detail_frame)
        harmony_frame.grid(row=len(colors), column=0, sticky="w", pady=10)
        
        tk.Label(harmony_frame, text="Color Harmony Tips:", 
                font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky="w")
        
        tips = [
            "• Analogous colors are next to each other on the wheel",
            "• Complementary colors are opposite each other",
            "• Triadic colors are evenly spaced around the wheel",
            "• Monochromatic uses shades of a single color"
        ]
        
        for i, tip in enumerate(tips):
            tk.Label(harmony_frame, text=tip, 
                    font=("Helvetica", 9), anchor="w").grid(row=i+1, column=0, sticky="w")


    def create_mannequin_image(self, top_hex, bottom_hex, shoes_hex):
        """Create a compact mannequin image"""
        # Reduce overall size
        img = Image.new("RGB", (300, 500), "#FFFFFF")
        draw = ImageDraw.Draw(img)
        
        # Compact coordinates
        body_parts = [
            # Head
            ("ellipse", (100, 30, 200, 130), "#FFDBAC"),
            # Neck
            ("rectangle", (130, 130, 170, 150), "#FFDBAC"),
            # Torso (shirt)
            ("rectangle", (80, 150, 220, 280), top_hex),
            # Left arm
            ("rectangle", (60, 160, 80, 270), top_hex),
            # Right arm
            ("rectangle", (220, 160, 240, 270), top_hex),
            # Left hand
            ("ellipse", (55, 260, 85, 290), "#FFDBAC"),
            # Right hand
            ("ellipse", (215, 260, 245, 290), "#FFDBAC"),
            # Pants
            ("rectangle", (80, 280, 220, 430), bottom_hex),
            # Left leg
            ("rectangle", (80, 430, 140, 480), bottom_hex),
            # Right leg
            ("rectangle", (160, 430, 220, 480), bottom_hex),
            # Left shoe
            ("rectangle", (70, 480, 140, 500), shoes_hex),
            # Right shoe
            ("rectangle", (160, 480, 230, 500), shoes_hex),
        ]
        
        # Draw all body parts
        for part in body_parts:
            shape, coords, color = part
            if shape == "ellipse":
                draw.ellipse(coords, fill=color, outline="black", width=2)
            else:
                draw.rectangle(coords, fill=color, outline="black", width=2)
        
        # Add details
        draw.line((130, 150, 170, 150), fill="black", width=2)  # Shoulders
        draw.arc((130, 100, 170, 140), start=0, end=180, fill="black", width=2)  # Neckline
        
        return img 

    def create_color_details(self, parent, top_color, bottom_color, shoes_color):
        """Create organized color details with proper spacing"""
        # Main container
        detail_frame = tk.Frame(parent)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Grid for color swatches
        colors = [
            ("Top Wear", top_color),
            ("Bottom Wear", bottom_color),
            ("Footwear", shoes_color)
        ]
        
        for i, (label, color) in enumerate(colors):
            # Create frame for each color
            color_frame = tk.Frame(detail_frame)
            color_frame.grid(row=i, column=0, sticky="w", pady=5)
            
            # Swatch
            tk.Frame(color_frame, width=30, height=30, bg=self.get_hex_color(color),
                    bd=1, relief=tk.SOLID).pack(side=tk.LEFT, padx=5)
            
            # Info labels
            info_frame = tk.Frame(color_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(info_frame, text=label, font=("Helvetica", 10, "bold"),
                    anchor="w").pack(fill=tk.X)
            tk.Label(info_frame, text=f"Color: {color.title()}", 
                    font=("Helvetica", 9), anchor="w").pack(fill=tk.X)
            tk.Label(info_frame, text=f"HEX: {self.get_hex_color(color)}", 
                    font=("Helvetica", 9), anchor="w").pack(fill=tk.X)
        
        # Add harmony suggestions
        harmony_frame = tk.Frame(detail_frame)
        harmony_frame.grid(row=len(colors), column=0, sticky="w", pady=(20, 10))
        
        tk.Label(harmony_frame, text="Suggested Color Combinations",
                font=("Helvetica", 10, "bold")).pack(anchor="w")
        
        self.create_harmony_suggestions(harmony_frame, 
                                    self.get_hex_color(top_color),
                                    self.get_hex_color(bottom_color),
                                    self.get_hex_color(shoes_color))
                                    
    def draw_color_wheel(self, canvas, top_hex, bottom_hex, shoes_hex):
        """Draw a complete color wheel showing the relationship between colors"""
        wheel_size = 300  # Reduced size for better fit
        center = wheel_size // 2
        radius = wheel_size // 2 - 20
        
        # Create color wheel image
        wheel_img = Image.new("RGBA", (wheel_size, wheel_size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(wheel_img)
        
        # Draw color wheel with thicker sectors (5° each)
        for angle in range(0, 360, 5):
            # Convert angle to HSV color
            h = angle / 360.0
            s = 1.0
            v = 1.0
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            color = (int(r*255), int(g*255), int(b*255))
            
            # Draw 5° sector
            draw.pieslice([(20, 20), (wheel_size-20, wheel_size-20)], 
                        angle, angle+5, fill=color, outline=color)
        
        # Convert to PhotoImage
        wheel_tk = ImageTk.PhotoImage(wheel_img)
        canvas.create_image(0, 0, image=wheel_tk, anchor="nw")
        canvas.wheel_img = wheel_tk  # Keep reference
        
        # Plot our colors on the wheel
        def plot_color(hex_color, name):
            r, g, b = self.hex_to_rgb(hex_color)
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            angle = h * 360
            rad = math.radians(angle)
            x = center + (radius * 0.8) * math.cos(rad)
            y = center + (radius * 0.8) * math.sin(rad)
            
            # Draw marker
            canvas.create_oval(x-8, y-8, x+8, y+8, 
                            fill=hex_color, outline="black", width=2)
            canvas.create_text(x, y+15, text=name, font=("Arial", 9, "bold"))
        
        plot_color(top_hex, "Top")
        plot_color(bottom_hex, "Bottom")
        plot_color(shoes_hex, "Shoes")
    def create_harmony_suggestions(self, parent, top_hex, bottom_hex, shoes_hex):
        """Create meaningful color harmony suggestions"""
        suggestions_frame = tk.Frame(parent, bg="white")
        suggestions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get HSV values for all colors
        def hex_to_hsv(hex_color):
            r, g, b = self.hex_to_rgb(hex_color)
            return colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        top_hsv = hex_to_hsv(top_hex)
        bottom_hsv = hex_to_hsv(bottom_hex)
        shoes_hsv = hex_to_hsv(shoes_hex)
        
        # Calculate hue differences
        top_bottom_diff = min(abs(top_hsv[0] - bottom_hsv[0]), 1 - abs(top_hsv[0] - bottom_hsv[0]))
        top_shoes_diff = min(abs(top_hsv[0] - shoes_hsv[0]), 1 - abs(top_hsv[0] - shoes_hsv[0]))
        bottom_shoes_diff = min(abs(bottom_hsv[0] - shoes_hsv[0]), 1 - abs(bottom_hsv[0] - shoes_hsv[0]))
        
        # Determine harmony type
        harmony_type = ""
        if top_bottom_diff < 0.1 and top_shoes_diff < 0.1:
            harmony_type = "Monochromatic"
        elif 0.45 < top_bottom_diff < 0.55:
            harmony_type = "Complementary"
        elif 0.15 < top_bottom_diff < 0.25:
            harmony_type = "Analogous"
        elif (0.3 < top_bottom_diff < 0.4) and (0.3 < top_shoes_diff < 0.4):
            harmony_type = "Triadic"
        else:
            harmony_type = "Eclectic"
        
        # Create suggestion text
        suggestions = {
            "Monochromatic": "Great monochromatic look! Try adding a contrasting accessory for visual interest.",
            "Complementary": "Bold complementary colors! Consider using one as the dominant and the other as accent.",
            "Analogous": "Harmonious analogous scheme. Add a neutral accessory to balance the look.",
            "Triadic": "Vibrant triadic harmony! Make sure one color dominates and the others support.",
            "Eclectic": "Eclectic color mix! Add a unifying neutral to tie the look together."
        }
        
        # Display harmony type
        tk.Label(suggestions_frame, text=f"Color Harmony: {harmony_type}", 
                font=("Helvetica", 11, "bold"), bg="white").pack(anchor="w", pady=(0, 10))
        
        # Display suggestion
        tk.Label(suggestions_frame, text=suggestions[harmony_type], 
                font=("Helvetica", 10), bg="white", wraplength=350, justify="left").pack(anchor="w")
        
        # Add specific color tips
        tips_frame = tk.Frame(suggestions_frame, bg="white")
        tips_frame.pack(anchor="w", pady=(15, 0))
        
        tk.Label(tips_frame, text="Color Tips:", 
                font=("Helvetica", 10, "bold"), bg="white").grid(row=0, column=0, sticky="w")
        
        tips = [
            f"• {self.get_color_tip(top_hex)} (Top)",
            f"• {self.get_color_tip(bottom_hex)} (Bottom)",
            f"• {self.get_color_tip(shoes_hex)} (Shoes)"
        ]
        
        for i, tip in enumerate(tips):
            tk.Label(tips_frame, text=tip, 
                    font=("Helvetica", 9), bg="white", anchor="w").grid(row=i+1, column=0, sticky="w")

    def get_color_tip(self, hex_color):
        """Get fashion tip for a specific color"""
        r, g, b = self.hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        if v < 0.2:  # Very dark
            return "Dark color - pairs well with bright accents"
        elif v > 0.8:  # Very light
            return "Light color - great for summer looks"
        elif s < 0.3:  # Desaturated
            return "Neutral tone - versatile for any occasion"
        elif h < 0.1 or h > 0.9:  # Reds/pinks
            return "Warm tone - energizing and attention-grabbing"
        elif 0.2 < h < 0.4:  # Yellows/greens
            return "Fresh color - perfect for daytime looks"
        else:  # Blues/purples
            return "Cool tone - calming and professional"    

    def create_color_swatch(self, parent, label, color_name, hex_color, row):
        """Create a color swatch with information"""
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        # Color swatch
        swatch = tk.Frame(frame, width=50, height=50, bg=hex_color, bd=1, relief=tk.SOLID)
        swatch.pack(side=tk.LEFT, padx=5)
        
        # Color information
        info_frame = tk.Frame(frame, bg="white")
        info_frame.pack(side=tk.LEFT)
        
        tk.Label(info_frame, text=f"{label}: {color_name.capitalize()}", 
                font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        tk.Label(info_frame, text=f"HEX: {hex_color}", font=("Arial", 9), bg="white").pack(anchor="w")
        
        # RGB values
        r, g, b = self.hex_to_rgb(hex_color)
        tk.Label(info_frame, text=f"RGB: {r}, {g}, {b}", font=("Arial", 9), bg="white").pack(anchor="w")

    def show_complementary_colors(self, parent, top_hex, bottom_hex, shoes_hex):
        """Show complementary color suggestions"""
        comp_frame = tk.Frame(parent, bg="white")
        comp_frame.pack(pady=10)
        
        # Get complementary colors
        top_comp = self.get_complementary(top_hex)
        bottom_comp = self.get_complementary(bottom_hex)
        shoes_comp = self.get_complementary(shoes_hex)
        
        # Create complementary color displays
        self.create_complementary_swatch(comp_frame, "Top", top_hex, top_comp, 0)
        self.create_complementary_swatch(comp_frame, "Bottom", bottom_hex, bottom_comp, 1)
        self.create_complementary_swatch(comp_frame, "Shoes", shoes_hex, shoes_comp, 2)
        
        # Add suggestion text
        tk.Label(parent, 
                text="Try using complementary colors for accessories or accent pieces",
                font=("Arial", 9, "italic"), bg="white").pack(pady=5)

    def create_complementary_swatch(self, parent, label, color_hex, comp_hex, row):
        """Create a complementary color display"""
        frame = tk.Frame(parent, bg="white")
        frame.grid(row=row, column=0, padx=10, pady=5, sticky="w")
        
        tk.Label(frame, text=f"{label}:", font=("Arial", 9), bg="white").pack(side=tk.LEFT)
        
        # Original color
        orig = tk.Frame(frame, width=40, height=40, bg=color_hex, bd=1, relief=tk.SOLID)
        orig.pack(side=tk.LEFT, padx=5)
        
        # Complementary color
        comp = tk.Frame(frame, width=40, height=40, bg=comp_hex, bd=1, relief=tk.SOLID)
        comp.pack(side=tk.LEFT, padx=5)

    def create_outfit_image(self, top_hex, bottom_hex, shoes_hex):
        """Create a simple outfit visualization"""
        # Create a blank image
        img = Image.new("RGB", (300, 400), "white")
        draw = ImageDraw.Draw(img)
        
        # Draw a simple outfit silhouette
        # Head
        draw.ellipse((100, 50, 200, 150), outline="black", width=2)
        
        # Top (shirt)
        draw.rectangle((100, 150, 200, 250), fill=top_hex, outline="black", width=2)
        
        # Bottom (pants)
        draw.polygon([(100, 250), (200, 250), (180, 350), (120, 350)], 
                    fill=bottom_hex, outline="black", width=2)
        
        # Shoes
        draw.rectangle((120, 350, 140, 370), fill=shoes_hex, outline="black", width=2)
        draw.rectangle((160, 350, 180, 370), fill=shoes_hex, outline="black", width=2)
        
        return img

    def get_complementary(self, hex_color):
        """Get complementary color for a given hex color"""
        r, g, b = self.hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        comp_h = (h + 0.5) % 1.0
        comp_r, comp_g, comp_b = colorsys.hsv_to_rgb(comp_h, s, v)
        return self.rgb_to_hex((int(comp_r*255), int(comp_g*255), int(comp_b*255)))

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color"""
        return '#%02x%02x%02x' % rgb

    def extract_color(self, item_name):
        if '(' in item_name and ')' in item_name:
            return item_name.split(' (')[1].rstrip(')')
        return "white"

    def get_hex_color(self, color_name):
        return self.color_map.get(color_name.lower(), "#FFFFFF")

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
   
if __name__ == "__main__":
    root = tk.Tk()
    app = WardrobeApp(root)
    root.mainloop()
import json
import random
import os
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

# --- Data Loading ---
with open("verbs-fr.json", encoding="utf-8") as f:
    verbs_data = json.load(f)

with open("top-verbs-fr.json", encoding="utf-8") as f:
    top_verbs_data = json.load(f)

with open("conjugation-fr.json", encoding="utf-8") as f:
    conjugation_data = json.load(f)

with open("not-reflexive.json", encoding="utf-8") as f:
    not_reflexive_verbs = json.load(f)

# Extract all valid verbs for both sets
# Extract all valid verbs for both sets
all_verbs = list(set(list(verbs_data.keys()) + [k.replace(":", "") for k in conjugation_data if ":" in k]))

# Handle top verbs - use the combined list from top_verbs_data
top_verbs_list = top_verbs_data["top_verbs"] + top_verbs_data["dr_mrs_vandertramp"]
top_verbs = [verb for verb in top_verbs_list if verb in all_verbs]  # Only keep verbs that exist in our full conjugation data

# --- Original Variables ---      

all_subjects = ["je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles"]
imperative_subjects = ["tu", "nous", "vous"]
reflexive_pronouns = {
    "je": "me", "tu": "te", "il": "se", "elle": "se", "on": "se",
    "nous": "nous", "vous": "vous", "ils": "se", "elles": "se"
}
subject_order = ["je", "tu", "il/elle/on", "nous", "vous", "ils/elles"]

mood_tense_map = {
    "indicative": ["present", "imperfect", "future", "simple-past", "past-perfect", "pluperfect", "future-perfect"],
    "conditional": ["present", "past"],
    "subjunctive": ["present", "imperfect", "past", "pluperfect"],
    "imperative": ["imperative-present"]
}

compound_tenses = {
    "indicative": {
        "past-perfect": "present",
        "pluperfect": "imperfect",
        "future-perfect": "future"
    },
    "conditional": {
        "past": "present"
    },
    "subjunctive": {
        "past": "present",
        "pluperfect": "imperfect"
    }
}

french_mood_labels = {
    "indicative": "indicatif",
    "conditional": "conditionnel",
    "subjunctive": "subjonctif",
    "imperative": "impératif"
}

french_tense_labels = {
    "present": "présent",
    "imperfect": "imparfait",
    "future": "futur",
    "simple-past": "passé simple",
    "past-perfect": "passé composé",
    "pluperfect": "plus-que-parfait",
    "future-perfect": "futur antérieur",
    "past": "passé",
    "imperative-present": "présent"
}

# Create a flat list of all (mood, tense) pairs
all_mood_tense_pairs = []
for mood, tenses in mood_tense_map.items():
    for tense in tenses:
        all_mood_tense_pairs.append((mood, tense))

##Weighted tenses:
# Example: Give compound tenses double weight
#all_mood_tense_pairs = []
#for mood, tenses in mood_tense_map.items():
#    for tense in tenses:
#        weight = 2 if tense in compound_tenses.get(mood, {}) else 1
#        weighted_mood_tense_pairs.extend([(mood, tense)] * weight)

# Extract all valid verbs
all_verbs = list(set(list(verbs_data.keys()) + [k.replace(":", "") for k in conjugation_data if ":" in k]))

# --- Original Functions ---
def find_group(verb):
    for key in conjugation_data:
        if ":" not in key:
            continue
        prefix, root = key.split(":")
        if verb == prefix + root:
            return key
    return None

def get_json_index(mood, subject):
    if mood == "imperative":
        return imperative_subjects.index(subject)
    if subject in ["il", "elle", "on"]:
        return subject_order.index("il/elle/on")
    if subject in ["ils", "elles"]:
        return subject_order.index("ils/elles")
    return subject_order.index(subject)

def get_gender_number_index(subject):
    if subject == "ils":
        return 1  # masculine plural
    elif subject == "elles":
        return 3  # feminine plural
    elif subject == "elle":
        return 2  # feminine singular
    else:
        return 0  # masculine singular

def get_auxiliary(verb, is_reflexive):
    if is_reflexive:
        return "être"
    if verb in verbs_data:
        return verbs_data[verb].get("aux", "avoir")
    return "avoir"

def get_participle(verb, subject, is_reflexive):
    if verb in verbs_data:
        template = verbs_data[verb]["t"]
        prefix = verb[:-len(template.split(":")[1])]
    else:
        template = find_group(verb)
        if not template:
            raise ValueError(f"No group found for {verb}")
        prefix = template.split(":")[0]

    forms = conjugation_data[template]["participle"]["past-participle"]
    if not isinstance(forms, list):
        raise ValueError(f"Expected list for past-participle of {verb}")
    if is_reflexive or get_auxiliary(verb, is_reflexive) == "être":
        index = get_gender_number_index(subject)
    else:
        index = 0  # default to masculine singular
    return prefix + forms[index]["i"]

def conjugate_simple(verb, mood, tense, subject):
    if verb in verbs_data:
        template = verbs_data[verb]["t"]
        prefix = verb[:-len(template.split(":")[1])]
    else:
        template = find_group(verb)
        if not template:
            raise ValueError(f"No group for {verb}")
        prefix = template.split(":")[0]

    forms = conjugation_data[template][mood][tense]
    index = get_json_index(mood, subject)
    form = forms[index]["i"]
    if isinstance(form, list):
        form = form[0]
    return prefix + form

def conjugate_compound(verb, mood, tense, subject, is_reflexive):
    aux_verb = get_auxiliary(verb, is_reflexive)
    aux_mood = mood
    aux_tense = compound_tenses[mood][tense]
    aux_form = conjugate_simple(aux_verb, aux_mood, aux_tense, subject)
    participle = get_participle(verb, subject, is_reflexive)
    if is_reflexive:
        reflexive = reflexive_pronouns[subject]
        return f"{reflexive} {aux_form} {participle}"
    else:
        return f"{aux_form} {participle}"

# --- Achievement System ---
class AchievementSystem:
    def __init__(self):
        self.save_file = "achievements.json"
        self.gallery_window = None
        
        # Create achievement categories with all requested milestones
        self.achievement_categories = {
            "streak": {
                "name": "Streak",
                "milestones": [
                    (2, "2 Correct in a Row"),
                    (4, "4 Correct in a Row"), 
                    (6, "6 Correct in a Row"),
                    (8, "8 Correct in a Row"),
                    (10, "10 Correct in a Row"), 
                    (20, "20 Correct in a Row"),
                    (30, "30 Correct in a Row"),
                    (50, "50 Correct in a Row"),
                ]
            },
            "total": {
                "name": "Total Correct",
                "milestones": [
                    (5, "5 Total Correct"),
                    (10, "10 Total Correct"),
                    (20, "20 Total Correct"),
                    (40, "40 Total Correct"),
                    (80, "80 Total Correct"),
                    (100, "100 Total Correct"),
                    (200, "200 Total Correct"),
                    (300, "300 Total Correct"),
                    (500, "500 Total Correct"),
                    (1000, "1000 Total Correct"),
                ]
            }
        }
        
        # Add mood+tense combinations with proper comma separation
        for mood, tenses in mood_tense_map.items():
            for tense in tenses:
                key = f"tense_{mood}_{tense}"
                self.achievement_categories[key] = {
                    "name": f"{french_mood_labels[mood]} - {french_tense_labels[tense]} Practice",
                    "milestones": [
                        (1, f"1 {french_mood_labels[mood]} - {french_tense_labels[tense]} Verb"),
                        (5, f"5 {french_mood_labels[mood]} - {french_tense_labels[tense]} Verbs"),
                        (15, f"15 {french_mood_labels[mood]} - {french_tense_labels[tense]} Verbs"),
                        (30, f"30 {french_mood_labels[mood]} - {french_tense_labels[tense]} Verbs"),
                        (50, f"50 {french_mood_labels[mood]} - {french_tense_labels[tense]} Verbs"),
                        (100, f"100 {french_mood_labels[mood]} - {french_tense_labels[tense]} Verbs"),
                        (250, f"250 {french_mood_labels[mood]} - {french_tense_labels[tense]} Verbs")
                    ]
                }
        
        # Load progress
        self.load_progress()
        
        # Distribute images to achievements
        self.assign_images_to_achievements()
    
    def all_achievements_completed(self):
        """Check if all achievements have been earned"""
        total_achievements = sum(len(cat["milestones"]) for cat in self.achievement_categories.values())
        return len(self.earned_achievements) >= total_achievements

    def assign_images_to_achievements(self):
        """Divide images evenly among achievement categories"""
        all_images = sorted([f for f in os.listdir("Monet-GIF") if f.lower().endswith('.gif')])
        images_per_category = len(all_images) // len(self.achievement_categories)
        
        self.achievement_images = {}
        for i, category in enumerate(self.achievement_categories):
            start_idx = i * images_per_category
            end_idx = start_idx + images_per_category
            self.achievement_images[category] = [
                os.path.join("Monet-GIF", f) 
                for f in all_images[start_idx:end_idx]
            ]
    
    def load_progress(self):
        """Load saved progress from file"""
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                    self.earned_achievements = set(tuple(x) for x in data.get("earned", []))
                    self.counters = data.get("counters", {})
                    # Store unlocked images as list of tuples (path, description)
                    self.unlocked_images = [(img, desc) for img, desc in data.get("unlocked_images", [])]
            else:
                self.reset_progress()
        except:
            self.reset_progress()
    
    def save_progress(self):
        """Save current progress to file"""
        with open(self.save_file, 'w') as f:
            json.dump({
                "earned": list(self.earned_achievements),
                "counters": self.counters,
                "unlocked_images": self.unlocked_images  # Save as list of tuples
            }, f)
    
    def reset_progress(self):
        """Initialize fresh progress"""
        self.earned_achievements = set()
        self.counters = {category: 0 for category in self.achievement_categories}
        self.unlocked_images = []  # Now a list of tuples
    
    def update_counters(self, streak, total, mood, tense):
        """Update all relevant counters"""
        self.counters["streak"] = streak
        self.counters["total"] = total
        tense_key = f"tense_{mood}_{tense}"
        if tense_key in self.counters:
            self.counters[tense_key] += 1
    
    def check_achievements(self):
        """Check if any new achievements were earned"""
        new_achievements = []
        
        for category, data in self.achievement_categories.items():
            current_value = self.counters.get(category, 0)
            
            for threshold, description in data["milestones"]:
                achievement_key = (category, threshold)
                
                if (current_value >= threshold and 
                    achievement_key not in self.earned_achievements):
                    
                    # Earn the achievement
                    self.earned_achievements.add(achievement_key)
                    
                    # Unlock a random image
                    available_images = [
                        img for img in self.achievement_images.get(category, [])
                        if img not in [u[0] for u in self.unlocked_images]
                    ]
                    
                    if available_images:
                        unlocked_image = random.choice(available_images)
                        self.unlocked_images.append((unlocked_image, description))
                        new_achievements.append({
                            "image": unlocked_image,
                            "description": description,
                            "category": data["name"]
                        })
        
        if new_achievements:
            self.save_progress()
        
        return new_achievements
# --- Quiz App ---
class ConjugationQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CouCou Conjugasion")
        self.root.minsize(800, 450)
        self.win_bg_image = None
        
        # Verb selection mode
        self.use_top_verbs = False  # Default to all verbs
        self.current_verb_set = all_verbs
        
        # Initialize systems
        self.achievement_system = AchievementSystem()
        self.score = 0
        self.total = 0
        self.streak = 0
        self.submitted = False
        
        # Font setup
        try:
            self.header_font = ("Futura", 14, "bold")
            self.main_font = ("Futura", 14)
            self.button_font = ("Futura", 12)
            self.accent_font = ("Futura", 12)
            tk.Label(root, text="test", font=self.header_font).destroy()
        except:
            self.header_font = ("Arial", 14, "bold")
            self.main_font = ("Arial", 14)
            self.button_font = ("Arial", 12)
            self.accent_font = ("Arial", 12)

        # Set up main window with properly sized background
        self.setup_main_window()
        
        # UI Setup
        self.setup_ui()
        self.generate_question()

    def setup_main_window(self):
        """Set up the main window with properly sized background"""
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        
        # Load background image
        try:
            self.bg_image = tk.PhotoImage(file="Claude_Monet_-_Jardin_à_Sainte-Adresse_bg.gif")
            
            # Create canvas for background
            self.bg_canvas = tk.Canvas(self.main_frame)
            self.bg_canvas.pack(fill="both", expand=True)
            
            # Add image to canvas
            self.bg_canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="bg")
            
            # Bind canvas resize to scale image
            self.bg_canvas.bind("<Configure>", self.resize_background)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.main_frame.configure(bg="#F7F6F2")
        
        # Create content frame (on top of background)
        self.content_frame = tk.Frame(self.main_frame, bg='white', bd=5, relief='groove')
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center", width=700, height=400)

    def resize_background(self, event):
        """Resize background image to fit canvas"""
        try:
            self.bg_canvas.delete("bg")
            # Create scaled version (simple approach without PIL)
            self.scaled_bg = self.bg_image.subsample(
                max(1, int(self.bg_image.width()/event.width)),
                max(1, int(self.bg_image.height()/event.height))
            )
            self.bg_canvas.create_image(0, 0, image=self.scaled_bg, anchor="nw", tags="bg")
        except Exception as e:
            print(f"Error resizing background: {e}")

    def setup_ui(self):
        # Top frame with score and buttons
        self.top_frame = tk.Frame(self.content_frame, bg="white")
        self.top_frame.pack(fill="x", pady=5)

        # Add verb set toggle button next to gallery button
        self.verb_set_button = tk.Button(
            self.top_frame, 
            text="🔀 Common Verbs", 
            font=self.button_font, 
            command=self.toggle_verb_set,
            bg="#DDE8CC",
            relief="ridge",
            borderwidth=2)
        self.verb_set_button.pack(side="right", padx=10)

        self.score_label = tk.Label(
            self.top_frame, 
            text=f"Score: {self.score}", 
            font=self.header_font, 
            bg="white"
        )
        self.score_label.pack(side="left", padx=10)

        self.streak_label = tk.Label(
            self.top_frame,
            text="🔥 0",
            font=self.header_font,
            bg="white",
            fg="#FF6B6B"
        )
        self.streak_label.pack(side="left", padx=10)

        # Gallery button
        unlocked_count = len(self.achievement_system.unlocked_images)
        total_images = sum(len(imgs) for imgs in self.achievement_system.achievement_images.values())
        self.gallery_button = tk.Button(
            self.top_frame, 
            text=f"🎨 Gallery ({unlocked_count}/{total_images})", 
            font=self.button_font, 
            command=self.show_gallery, 
            bg="#DDE8CC",
            relief="ridge",
            borderwidth=2
        )
        self.gallery_button.pack(side="right", padx=10)

        # Question label
        self.question_label = tk.Label(
            self.content_frame, 
            text="", 
            font=self.main_font, 
            bg="white",
            wraplength=600
        )
        self.question_label.pack(pady=5)

        # Answer entry
        self.answer_entry = tk.Entry(
            self.content_frame, 
            font=self.main_font, 
            relief="groove", 
            borderwidth=3,
            width=40
        )
        self.answer_entry.pack(pady=5)
        self.answer_entry.focus_set()

        # Accent buttons frame
        self.accent_frame = tk.Frame(self.content_frame, bg="white")
        self.accent_frame.pack(pady=5)

        accents = ['é', 'è', 'ê', 'ë', 'à', 'ç', 'ô', 'ù', 'î', 'ï', 'â', 'û']
        for i, char in enumerate(accents):
            b = tk.Button(
                self.accent_frame, 
                text=char, 
                width=2, 
                font=self.accent_font, 
                command=lambda c=char: self.insert_accent(c), 
                bg="#E7E6E1", 
                relief="ridge", 
                borderwidth=2
            )
            b.grid(row=0, column=i, padx=1)

        # Submit button
        self.submit_button = tk.Button(
            self.content_frame, 
            text="Submit", 
            command=self.submit_or_next, 
            font=self.button_font, 
            bg="#A8C686",
            relief="ridge",
            borderwidth=3
        )
        self.submit_button.pack(pady=10)

        # Feedback label
        self.feedback_label = tk.Label(
            self.content_frame, 
            text="", 
            font=self.main_font, 
            bg="white"
        )
        self.feedback_label.pack(pady=5)

        self.root.bind("<Return>", self.submit_or_next)

    def insert_accent(self, character):
        pos = self.answer_entry.index(tk.INSERT)
        current = self.answer_entry.get()
        new = current[:pos] + character + current[pos:]
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.insert(0, new)
        self.answer_entry.icursor(pos + 1)
            
    def toggle_verb_set(self):
        """Switch between all verbs and top/common verbs"""
        self.use_top_verbs = not self.use_top_verbs
        if self.use_top_verbs:
            self.current_verb_set = top_verbs
            self.verb_set_button.config(text="🔀 All Verbs")
        else:
            self.current_verb_set = all_verbs
            self.verb_set_button.config(text="🔀 Common Verbs")

        # Regenerate question with new verb set
        self.generate_question()

    def generate_question(self):
        self.submitted = False
        self.answer_entry.config(state="normal")
        self.answer_entry.delete(0, tk.END)
        self.feedback_label.config(text="")

        self.verb = random.choice(self.current_verb_set)
        
        # This ensures equal probability for each tense across all moods
        self.mood, self.tense = random.choice(all_mood_tense_pairs)        
        self.subject = random.choice(imperative_subjects if self.mood == "imperative" else all_subjects)
        self.is_reflexive = (self.verb not in not_reflexive_verbs and self.mood != "imperative" and random.random() < 0.15)

        try:
            if self.tense in compound_tenses.get(self.mood, {}):
                self.answer = conjugate_compound(self.verb, self.mood, self.tense, self.subject, self.is_reflexive)
            else:
                self.answer = conjugate_simple(self.verb, self.mood, self.tense, self.subject)
                if self.is_reflexive:
                    pronoun = reflexive_pronouns[self.subject]
                    self.answer = f"{pronoun} {self.answer}"
        except Exception as e:
            print(f"Skipping question due to error: {e}")
            self.generate_question()
            return

        display_mood = french_mood_labels.get(self.mood, self.mood)
        display_tense = french_tense_labels.get(self.tense, self.tense)
        prompt = f"Conjuguez '{self.verb}'"
        if self.is_reflexive:
            prompt += " (réflexif)"
        prompt += f" au {display_mood} - {display_tense}, sujet : '{self.subject}'"
        self.question_label.config(text=prompt)

    def show_gallery(self):
        """Show unlocked achievements in a grid with descriptions"""
        if hasattr(self.achievement_system, 'gallery_window') and self.achievement_system.gallery_window and self.achievement_system.gallery_window.winfo_exists():
            self.achievement_system.gallery_window.lift()
            return
            
        gallery_window = tk.Toplevel(self.root)
        gallery_window.title("Achievement Gallery")
        gallery_window.minsize(600, 500)
        gallery_window.geometry("800x600")
        self.achievement_system.gallery_window = gallery_window
        
        # Make sure window closes properly
        gallery_window.protocol("WM_DELETE_WINDOW", lambda: self.close_gallery(gallery_window))
        
        # Create main frame with background
        main_frame = tk.Frame(gallery_window)
        main_frame.pack(fill="both", expand=True)
        
        # Load background image
        try:
            bg_image = tk.PhotoImage(file="Claude_Monet_-_Jardin_à_Sainte-Adresse_bg.gif")
            
            # Create canvas for background
            bg_canvas = tk.Canvas(main_frame)
            bg_canvas.pack(fill="both", expand=True)
            
            # Add image to canvas
            bg_canvas.create_image(0, 0, image=bg_image, anchor="nw", tags="bg")
            self.gallery_bg_image = bg_image  # Keep reference
            
            def resize_bg(event):
                try:
                    bg_canvas.delete("bg")
                    scaled_bg = bg_image.subsample(
                        max(1, int(bg_image.width()/event.width)),
                        max(1, int(bg_image.height()/event.height))
                    )
                    bg_canvas.create_image(0, 0, image=scaled_bg, anchor="nw", tags="bg")
                except:
                    pass
            
            bg_canvas.bind("<Configure>", resize_bg)
            
        except Exception as e:
            print(f"Error loading background image: {e}")
            main_frame.configure(bg="#F7F6F2")
        
        # Create content frame (white panel)
        content_frame = tk.Frame(main_frame, bg='white', bd=5, relief='groove')
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=750, height=550)
        
        # Title label
        tk.Label(content_frame, 
                text="Achievement Gallery", 
                font=self.header_font, 
                bg="white").pack(pady=10)
        
        # Create container for canvas and scrollbar
        container = tk.Frame(content_frame, bg='white')
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create frame inside canvas
        scroll_frame = tk.Frame(canvas, bg='white')
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Update scroll region when frame size changes
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scroll_frame.bind("<Configure>", update_scrollregion)
        
        # Create 4x30 grid (4 columns, 30 rows)
        cols = 4
        rows = 30
        square_size = 160
        self.achievement_img_refs = []  # This will store our image references
        
        unlocked_images = self.achievement_system.unlocked_images  # List of (path, description) tuples
        total_squares = cols * rows
        
        for i in range(total_squares):
            row = i // cols
            col = i % cols
            
            # Create frame for each achievement square
            frame = tk.Frame(scroll_frame, 
                            width=square_size, 
                            height=square_size + 40,
                            bg="#E0E0E0", 
                            highlightbackground="black", 
                            highlightthickness=1)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            frame.grid_propagate(False)
            
            # Image container (fixed size)
            img_container = tk.Frame(frame, 
                                   width=square_size-10, 
                                   height=square_size-10,
                                   bg="#E0E0E0")
            img_container.grid(row=0, column=0, sticky='nsew', pady=(10,5), padx=(2,3))
            img_container.pack_propagate(False)
            
            if i < len(unlocked_images):
                img_path, description = unlocked_images[i]
                
                try:
                    # Load the image
                    img = tk.PhotoImage(file=img_path)
                    
                    # Create a canvas for the image (instead of a label)
                    img_canvas = tk.Canvas(img_container, 
                                          width=square_size-10, 
                                          height=square_size-10,
                                          bg="#E0E0E0",
                                          highlightthickness=0)
                    img_canvas.pack(expand=True)
                    
                    # Calculate scaling to fit while maintaining aspect ratio
                    img_width = img.width()
                    img_height = img.height()
                    
                    # Calculate the scaling factor
                    scale = min((square_size-10)/img_width, (square_size-10)/img_height)
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    # Calculate position to center the image
                    x_pos = ((square_size-10) - new_width) // 2
                    y_pos = ((square_size-10) - new_height) // 2
                    
                    # Create the scaled image
                    resized_img = img.subsample(
                        max(1, int(img.width()/new_width)),
                        max(1, int(img.height()/new_height))
                    )
                    
                    # Add image to canvas at calculated position
                    img_canvas.create_image(x_pos, y_pos, anchor="nw", image=resized_img)
                    
                    # Store the image reference to prevent garbage collection
                    self.achievement_img_refs.append(resized_img)
                    
                    # Display description below image
                    desc_label = tk.Label(frame, 
                                        text=description, 
                                        wraplength=square_size-20,
                                        font=('Arial', 8),
                                        bg="#E0E0E0")
                    desc_label.grid(row=1, column=0, sticky='nsew', pady=(5,0))
                    
                except Exception as e:
                    print(f"Error loading image {img_path}: {e}")
                    tk.Label(img_container, text="?", bg="#E0E0E0").pack(expand=True)
            else:
                # Empty square
                tk.Label(img_container, text="", bg="#E0E0E0").pack(expand=True)
        
        # Configure grid weights
        for i in range(cols):
            scroll_frame.columnconfigure(i, weight=1)
        for i in range(rows):
            scroll_frame.rowconfigure(i, weight=1)
        
        # Display progress text
        progress_label = tk.Label(content_frame,
                                text=f"Unlocked: {len(unlocked_images)}/{total_squares}",
                                font=self.main_font,
                                bg="white")
        progress_label.pack(side="bottom", pady=10)
        
    def close_gallery(self, window):
        """Properly close the gallery window"""
        window.destroy()
        self.achievement_system.gallery_window = None
        
    def check_background_update(self):
        """Check if we should switch to the win background"""
        if self.achievement_system.all_achievements_completed():
            try:
                self.win_bg_image = tk.PhotoImage(file="win-bg.gif")
                self.bg_canvas.itemconfig("bg", image=self.win_bg_image)
            except Exception as e:
                print(f"Error loading win background: {e}")

    def submit_or_next(self, event=None):
        if not self.submitted:
            user_input = self.answer_entry.get().strip().lower()
            if not user_input:
                return
                
            self.submitted = True
            self.total += 1
            
            if user_input == self.answer.lower():
                self.feedback_label.config(text="✅ Correct!", fg="green")
                self.score += 1
                self.streak += 1
                
                # Update achievement counters
                self.achievement_system.update_counters(
                    self.streak,
                    self.score,
                    self.mood,  # Add this parameter
                    self.tense
                )
                
                # Check for new achievements
                new_achievements = self.achievement_system.check_achievements()

                # Check if we should update the background
                if new_achievements:
                    self.check_background_update()
                    
                # Notify about new achievements
                for achievement in new_achievements:
                    messagebox.showinfo(
                        "New Achievement!",
                        f"{achievement['description']}\n\n"
                        f"Category: {achievement['category']}"
                    )
                    
                # Update gallery button if new images unlocked
                if new_achievements:
                    unlocked_count = len(self.achievement_system.unlocked_images)
                    total_images = sum(len(imgs) for imgs in self.achievement_system.achievement_images.values())
                    self.gallery_button.config(
                        text=f"🎨 Gallery ({unlocked_count}/{total_images})"
                    )
            else:
                self.feedback_label.config(text=f"❌ Incorrect. Correct answer: {self.answer}", fg="red")
                self.streak = 0
            
            self.score_label.config(text=f"Score: {self.score}")
            self.streak_label.config(text=f"🔥 {self.streak}")
            self.answer_entry.config(state="disabled")
            self.submit_button.config(text="Next Question")
        else:
            self.generate_question()
            self.submit_button.config(text="Submit")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ConjugationQuizApp(root)
    root.mainloop()

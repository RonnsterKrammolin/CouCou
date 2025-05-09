from distutils.core import setup
import py2exe
import os

# List all data files (JSON and GIFs)
data_files = [
    ("", ["verbs-fr.json", "top-verbs-fr.json", "conjugation-fr.json", "not-reflexive.json"]),
    ("Monet-GIF", [os.path.join("Monet-GIF", f) for f in os.listdir("Monet-GIF") if f.endswith('.gif')]),
    ("", ["Claude_Monet_-_Jardin_à_Sainte-Adresse_bg.gif", "win-bg.gif"])
]

setup(
    name="CouCou Conjugasion",
    version="1.0",
    description="French Verb Conjugation Quiz",
    author="Perer M.",
    
    # Main script
    windows=[{
        "script": "your_main_script.py",  # Replace with your actual script filename
        "icon_resources": [(1, "your_icon.ico")]  # Optional: add if you have an icon
    }],
    
    options={
        "py2exe": {
            "includes": [
                "tkinter",
                "json",
                "random",
                "os",
                "pathlib",
                "tkinter.messagebox",
                "tkinter.ttk"
            ],
            "bundle_files": 1,  # Create single executable
            "compressed": True,  # Compress the library archive
            "optimize": 2,       # Optimize bytecode
            "dist_dir": "dist",  # Output directory
            "excludes": ["Tkconstants", "Tkinter", "tcl"],  # Exclude unnecessary modules
        }
    },
    
    # Include all data files
    data_files=data_files,
    
    # Don't create a library.zip file
    zipfile=None,
)

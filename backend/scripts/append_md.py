import os

files_to_merge = [
    "API_DOCUMENTATION.md",
    "DATABASE_MIGRATIONS.md",
    "MEDIUM_PRIORITY_NOTES.md",
    "PROJECT_STRUCTURE.md",
    "SECURITY.md"
]

readme_path = "p:\\Project\\MINI PROJECT\\AI RESEPTIONIST\\README.md"
base_dir = "p:\\Project\\MINI PROJECT\\AI RESEPTIONIST"

with open(readme_path, "a", encoding="utf-8") as readme:
    readme.write("\n\n---\n")
    readme.write("# APPENDIX: Consolidated Documentation\n\n")
    for f in files_to_merge:
        file_path = os.path.join(base_dir, f)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as src:
                readme.write(f"## {f}\n\n")
                readme.write(src.read())
                readme.write("\n\n---\n")

print("Merge complete.")

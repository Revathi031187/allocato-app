"""
Create outline.png (32x32) and color.png (192x192) for the Teams app package.
Run from the teams-app-package folder: python create_icons.py
Uses matplotlib (already in project requirements).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Outline: 32x32, simple icon
fig, ax = plt.subplots(figsize=(1, 1), dpi=32)
fig.patch.set_facecolor("#ffffff")
ax.set_facecolor("#6264A7")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.savefig("outline.png", bbox_inches="tight", pad_inches=0, dpi=32)
plt.close()

# Color: 192x192, full color icon
fig, ax = plt.subplots(figsize=(1, 1), dpi=192)
fig.patch.set_facecolor("#ffffff")
ax.set_facecolor("#6264A7")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.savefig("color.png", bbox_inches="tight", pad_inches=0, dpi=192)
plt.close()

print("Created outline.png (32x32) and color.png (192x192) in", SCRIPT_DIR)
print("Next: zip manifest.json, outline.png, and color.png (see README-PACKAGE.md)")

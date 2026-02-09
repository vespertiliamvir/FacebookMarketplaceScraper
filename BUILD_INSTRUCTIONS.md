# 📦 How to Build Executable (Windows)

This guide explains how to package the Facebook Marketplace Scraper as a standalone `.exe` file using `auto-py-to-exe`.

## 1. Prerequisites
Ensure you have the required packages installed:
```bash
pip install auto-py-to-exe pyinstaller
```

## 2. Launch Auto-Py-To-Exe
Run the following command in your terminal:
```bash
auto-py-to-exe
```
This will open a GUI window.

## 3. Configuration Steps

Fill in the fields as follows:

### **Script Location**
*   **Script Location**: Browse and select `repo/main.py`

### **Onefile vs One Directory**
*   Select **One File** (Creates a single `.exe` file)

### **Console Window**
*   Select **Console Based** (Important! We need the terminal for user input and colorful output)

### **Icon (Optional)**
*   You can select an `.ico` file if you have one.

### **Additional Files**
*   (None required - the script generates its own config/logs in the directory where it runs)

### **Advanced > Hidden Imports**
*   Click the `+` to add hidden imports. Add these just to be safe:
    *   `scraper.parallel_manager`
    *   `scraper.auth`
    *   `scraper.config`

## 4. Build
1.  Click the big blue **CONVERT .PY TO .EXE** button.
2.  Wait for the process to finish.
3.  Click **Open Output Folder**.

## 5. Running the Executable
*   You will find `main.exe` in the output folder.
*   You can rename it to `FacebookScraper.exe`.
*   **Important**: The first time you run it, it might trigger the "Login Setup" automatically if it doesn't find your Master Profile.
*   **Parallel Scraping**: If you use parallel scraping, the `.exe` will spawn multiple processes. This is normal.

## Troubleshooting
*   **"Failed to execute script main"**: Run the exe from a terminal (`cmd` or `powershell`) to see the actual error message.
*   **Virus Scan**: Sometimes unsigned `.exe` files from PyInstaller are flagged by Windows Defender. You may need to add an exclusion.

"""Diagnostic: check and test explorer-related registry keys on Windows 11."""
import winreg
import subprocess
import sys

HKCU = winreg.HKEY_CURRENT_USER

def read_reg(hive, path, name):
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception as e:
        return f"NOT FOUND ({e})"

def list_subkeys(hive, path):
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        i = 0
        names = []
        while True:
            try:
                names.append(winreg.EnumKey(key, i))
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
        return names
    except Exception as e:
        return [f"ERROR: {e}"]

def list_values(hive, path):
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        i = 0
        vals = []
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                vals.append(f"  {name} = {value}")
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
        return vals
    except Exception as e:
        return [f"ERROR: {e}"]

print("=" * 70)
print("DIAGNOSTIC: Explorer Registry Keys")
print("=" * 70)

# 1. Windows version
print("\n--- Windows Version ---")
print(f"  platform.version(): {sys.getwindowsversion()}")
build = sys.getwindowsversion().build
print(f"  Build number: {build}")

# 2. Recycle Bin CLSID root
clsid_root = r"Software\Classes\CLSID\{645FF040-5081-101B-9F08-00AA002F954E}"
print(f"\n--- CLSID Root: {clsid_root} ---")
vals = list_values(HKCU, clsid_root)
for v in vals:
    print(v)
if not vals:
    print("  (empty or not found)")

# 3. Recycle Bin ShellFolder
shell_folder = clsid_root + r"\ShellFolder"
print(f"\n--- ShellFolder: {shell_folder} ---")
vals = list_values(HKCU, shell_folder)
for v in vals:
    print(v)
if not vals:
    print("  (empty or not found)")

# 4. Explorer Desktop NameSpace
ns_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace"
print(f"\n--- Desktop NameSpace: {ns_path} ---")
subkeys = list_subkeys(HKCU, ns_path)
for sk in subkeys:
    print(f"  Subkey: {sk}")
if not subkeys:
    print("  (empty or not found)")

# 5. Explorer Advanced (TaskbarEndTask)
adv_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
print(f"\n--- Explorer Advanced (TaskbarEndTask) ---")
val = read_reg(HKCU, adv_key, "TaskbarEndTask")
print(f"  TaskbarEndTask = {val}")

# 6. Check if we can write (test write then delete)
print("\n--- Test Write ---")
test_path = r"Software\Classes\CLSID\{645FF040-5081-101B-9F08-00AA002F954E}"
try:
    key = winreg.CreateKey(HKCU, test_path)
    winreg.SetValueEx(key, "_TEST_WRITE_", 0, winreg.REG_DWORD, 999)
    winreg.CloseKey(key)
    # Read back
    val = read_reg(HKCU, test_path, "_TEST_WRITE_")
    print(f"  Write test: wrote 999, read back = {val}")
    # Delete test value
    key = winreg.OpenKey(HKCU, test_path, 0, winreg.KEY_SET_VALUE)
    winreg.DeleteValue(key, "_TEST_WRITE_")
    winreg.CloseKey(key)
    print("  Test value deleted successfully")
except Exception as e:
    print(f"  Write test FAILED: {e}")

# 7. Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
pinned = read_reg(HKCU, clsid_root, "System.IsPinnedToNameSpaceTree")
attrs = read_reg(HKCU, shell_folder, "Attributes")
task_end = read_reg(HKCU, adv_key, "TaskbarEndTask")

print(f"  System.IsPinnedToNameSpaceTree (CLSID root) = {pinned}")
print(f"  Attributes (ShellFolder) = {attrs}")
print(f"  TaskbarEndTask = {task_end}")
print(f"  Windows build = {build}")

if build >= 22631:
    print("  => Windows 11 23H2+ (Kill task should be supported)")
else:
    print("  => Windows 11 pre-23H2 (Kill task may not be supported)")

print()

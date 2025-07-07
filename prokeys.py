#!/usr/bin/env python3
"""
ProKeys - Clipboard Content Keystroke Emulator

This script reads content from the clipboard and emulates keystrokes to paste it
with accurate indentation and formatting. Useful for situations where standard
Ctrl+V doesn't work properly or when you need precise character-by-character pasting.

Usage:
    python prokeys.py [--delay DELAY] [--trigger-key KEY]

Options:
    --delay DELAY        Delay between keystrokes in seconds (default: 0.01)
    --trigger-key KEY    Key combination to trigger pasting (default: cmd+shift+v)
    --help              Show this help message
"""

import argparse
import time
import sys
import threading
import json
import os
from typing import Optional

try:
    import pyperclip
    import pynput
    from pynput import keyboard
    from pynput.keyboard import Key, Listener, KeyCode
    import pyautogui
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install them using: pip install pyperclip pynput pyautogui")
    sys.exit(1)


CONFIG_FILE = "prokeys_config.json"

# macOS US Keyboard Layout Character Mapping
# Maps characters to their corresponding base key and required modifiers
MACOS_KEY_MAPPING = {
    # Shift + Number row special characters
    '!': ('1', [Key.shift]),
    '@': ('2', [Key.shift]),
    '#': ('3', [Key.shift]),
    '$': ('4', [Key.shift]),
    '%': ('5', [Key.shift]),
    '^': ('6', [Key.shift]),
    '&': ('7', [Key.shift]),
    '*': ('8', [Key.shift]),
    '(': ('9', [Key.shift]),
    ')': ('0', [Key.shift]),
    
    # Uppercase letters (A-Z)
    'A': ('a', [Key.shift]), 'B': ('b', [Key.shift]), 'C': ('c', [Key.shift]), 'D': ('d', [Key.shift]),
    'E': ('e', [Key.shift]), 'F': ('f', [Key.shift]), 'G': ('g', [Key.shift]), 'H': ('h', [Key.shift]),
    'I': ('i', [Key.shift]), 'J': ('j', [Key.shift]), 'K': ('k', [Key.shift]), 'L': ('l', [Key.shift]),
    'M': ('m', [Key.shift]), 'N': ('n', [Key.shift]), 'O': ('o', [Key.shift]), 'P': ('p', [Key.shift]),
    'Q': ('q', [Key.shift]), 'R': ('r', [Key.shift]), 'S': ('s', [Key.shift]), 'T': ('t', [Key.shift]),
    'U': ('u', [Key.shift]), 'V': ('v', [Key.shift]), 'W': ('w', [Key.shift]), 'X': ('x', [Key.shift]),
    'Y': ('y', [Key.shift]), 'Z': ('z', [Key.shift]),
    
    # Additional special characters that require shift
    '_': ('-', [Key.shift]),  # Underscore: Shift + Hyphen
    '+': ('=', [Key.shift]),  # Plus: Shift + Equals
    '{': ('[', [Key.shift]),  # Left brace: Shift + Left bracket
    '}': (']', [Key.shift]),  # Right brace: Shift + Right bracket
    '|': ('\\', [Key.shift]), # Pipe: Shift + Backslash
    ':': (';', [Key.shift]),  # Colon: Shift + Semicolon
    '"': ("'", [Key.shift]),  # Double quote: Shift + Single quote
    '<': (',', [Key.shift]),  # Less than: Shift + Comma
    '>': ('.', [Key.shift]),  # Greater than: Shift + Period
    '?': ('/', [Key.shift]),  # Question mark: Shift + Slash
    '~': ('`', [Key.shift]),  # Tilde: Shift + Backtick
    
    # Numbers (no modifiers needed)
    '0': ('0', []), '1': ('1', []), '2': ('2', []), '3': ('3', []), '4': ('4', []),
    '5': ('5', []), '6': ('6', []), '7': ('7', []), '8': ('8', []), '9': ('9', []),
    
    # Lowercase letters (no modifiers needed)
    'a': ('a', []), 'b': ('b', []), 'c': ('c', []), 'd': ('d', []), 'e': ('e', []),
    'f': ('f', []), 'g': ('g', []), 'h': ('h', []), 'i': ('i', []), 'j': ('j', []),
    'k': ('k', []), 'l': ('l', []), 'm': ('m', []), 'n': ('n', []), 'o': ('o', []),
    'p': ('p', []), 'q': ('q', []), 'r': ('r', []), 's': ('s', []), 't': ('t', []),
    'u': ('u', []), 'v': ('v', []), 'w': ('w', []), 'x': ('x', []), 'y': ('y', []),
    'z': ('z', []),
    
    # Basic punctuation (no modifiers needed)
    ' ': (' ', []),           # Space
    '-': ('-', []),           # Hyphen
    '=': ('=', []),           # Equals
    '[': ('[', []),           # Left bracket
    ']': (']', []),           # Right bracket
    '\\': ('\\', []),         # Backslash
    ';': (';', []),           # Semicolon
    "'": ("'", []),           # Single quote
    ',': (',', []),           # Comma
    '.': ('.', []),           # Period
    '/': ('/', []),           # Slash
    '`': ('`', []),           # Backtick
}



def wpm_to_delay(wpm: int) -> float:
    """Convert WPM to delay between keystrokes in seconds.
    
    More realistic calculation accounting for:
    - Natural typing rhythm
    - Application processing time  
    - Keystroke simulation overhead
    """
    # Base calculation: 60 / (WPM * 5) but adjusted for realism
    base_delay = 60.0 / (wpm * 5)
    
    # Add realistic overhead (20-50% depending on speed)
    if wpm < 60:
        # Slower speeds: minimal overhead
        return base_delay * 1.2
    elif wpm < 120:
        # Moderate speeds: some overhead
        return base_delay * 1.3
    elif wpm < 200:
        # Fast speeds: more overhead needed
        return base_delay * 1.4
    else:
        # Very fast speeds: significant overhead
        return base_delay * 1.5

def delay_to_wpm(delay: float) -> int:
    """Convert delay to WPM (approximate reverse calculation)."""
    if delay <= 0:
        return 9999
    
    # Reverse calculation accounting for overhead
    # This is approximate since the original calculation has variable overhead
    base_wpm = 60.0 / (delay * 5)
    
    # Estimate overhead and adjust
    if delay > 0.3:  # Corresponds to ~40 WPM
        return int(base_wpm / 1.2)
    elif delay > 0.15:  # Corresponds to ~80 WPM  
        return int(base_wpm / 1.3)
    elif delay > 0.08:  # Corresponds to ~150 WPM
        return int(base_wpm / 1.4)
    else:
        return int(base_wpm / 1.5)

def load_config() -> dict:
    """Load configuration from config file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Default configuration
    return {
        "typing_speed_wpm": 250,
        "delay": wpm_to_delay(250),
        "trigger_key": "cmd+shift+v",
        "windows_mode": False
    }

def save_config(config: dict) -> bool:
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def validate_wpm(wpm: int) -> bool:
    """Validate WPM is in acceptable range."""
    return 99 <= wpm <= 5000

def set_typing_speed(wpm: int) -> bool:
    """Set typing speed in WPM."""
    if not validate_wpm(wpm):
        print(f"❌ Error: WPM must be between 99 and 5000. Got: {wpm}")
        return False
    
    config = load_config()
    config["typing_speed_wpm"] = wpm
    config["delay"] = wpm_to_delay(wpm)
    
    if save_config(config):
        print(f"✅ Typing speed set to {wpm} WPM")
        print(f"   Delay between keystrokes: {config['delay']:.4f} seconds")
        
        # Speed category
        if wpm < 30:
            category = "🐌 Very Slow"
        elif wpm < 60:
            category = "🚶 Slow"
        elif wpm < 120:
            category = "🚴 Moderate"
        elif wpm < 200:
            category = "🏃 Fast"
        elif wpm < 400:
            category = "🚀 Very Fast"
        else:
            category = "⚡ Lightning"
        
        print(f"   Speed category: {category}")
        return True
    else:
        return False

def show_config():
    """Display current configuration."""
    config = load_config()
    
    print("🎯 ProKeys Configuration")
    print("=" * 30)
    print(f"Typing Speed: {config['typing_speed_wpm']} WPM")
    print(f"Keystroke Delay: {config['delay']:.4f} seconds")
    print(f"Trigger Key: {config['trigger_key']}")
    
    # Speed reference
    print("\n📊 Speed Reference:")
    print("  99-149 WPM:   🚴 Moderate (recommended)")
    print(" 150-249 WPM:   🏃 Fast (may skip in some apps)")
    print(" 250-499 WPM:   🚀 Very Fast (for simple text)")
    print(" 500-999 WPM:   ⚡ Lightning (extreme speed)")
    print("1000-5000 WPM:  🚀💥 Ludicrous Speed (instant)")

def interactive_config():
    """Interactive configuration mode."""
    print("🎯 ProKeys Configuration")
    print("=" * 40)
    
    config = load_config()
    current_wpm = config["typing_speed_wpm"]
    
    print(f"Current typing speed: {current_wpm} WPM")
    print("\nSpeed recommendations:")
    print("  • 100-250 WPM: Best for most applications")
    print("  • 250-500 WPM: Faster but may skip in some apps")
    print("  • 500+ WPM: Very fast, simple text only")
    print("  • 1000+ WPM: Extreme speed")
    
    # Speed presets
    print("\n🚀 Quick Presets:")
    print("  [1] 100 WPM  - 🚴 Moderate")
    print("  [2] 250 WPM  - 🏃 Fast")
    print("  [3] 500 WPM  - 🚀 Very Fast")
    print("  [4] 1000 WPM - ⚡ Lightning")
    print("  [5] 2000 WPM - 🚀💥 Ludicrous")
    print("  [0] Custom WPM")
    
    while True:
        try:
            choice = input(f"\nSelect option (1-5 for presets, 0 for custom, Enter to cancel): ").strip()
            
            if not choice:
                print("No changes made.")
                return
            
            if choice == "1":
                wpm = 100
            elif choice == "2":
                wpm = 250
            elif choice == "3":
                wpm = 500
            elif choice == "4":
                wpm = 1000
            elif choice == "5":
                wpm = 2000
            elif choice == "0":
                custom_input = input("Enter custom WPM (99-5000): ").strip()
                if not custom_input:
                    print("No changes made.")
                    return
                wpm = int(custom_input)
            else:
                print("❌ Please enter a number between 0-5.")
                continue
            
            if validate_wpm(wpm):
                if set_typing_speed(wpm):
                    print("\n✅ Configuration updated successfully!")
                    return
                else:
                    print("\n❌ Failed to save configuration.")
                    return
            else:
                print(f"❌ Please enter a WPM between 99 and 5000.")
                
        except ValueError:
            print("❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nConfiguration cancelled.")
            return


class ProKeys:
    def __init__(self, delay: float = 0.01, trigger_key: str = "cmd+shift+v", windows_mode: bool = False, debug: bool = False):
        self.delay = delay
        self.trigger_key = trigger_key
        self.windows_mode = windows_mode
        self.debug = debug
        
        # Initialize both keyboard controllers for hybrid approach
        from pynput.keyboard import Controller
        self.keyboard_controller = Controller()  # For indentation handling
        
        # Use pynput for input listening (works well)
        self.listener = None
        self.running = False
        self.trigger_keys = self._parse_trigger_key(trigger_key)
        self.pressed_keys = set()
        
        # Configure PyAutoGUI for output (works better for character generation)
        pyautogui.PAUSE = 0.01  # Small pause between operations
        pyautogui.FAILSAFE = True  # Safety feature
        
        if self.debug:
            print("[DEBUG] ProKeys initialized with hybrid approach - pynput + PyAutoGUI")
        
        
    def _parse_trigger_key(self, trigger_key: str) -> set:
        """Parse trigger key combination string into a set of keys."""
        key_mapping = {
            'ctrl': Key.ctrl_l,
            'shift': Key.shift_l,
            'alt': Key.alt_l,
            'cmd': Key.cmd,  # Use Key.cmd (not cmd_l)
            'super': Key.cmd,
            'win': Key.cmd,
        }
        
        keys = trigger_key.lower().split('+')
        parsed_keys = set()
        
        for key in keys:
            key = key.strip()
            if key in key_mapping:
                parsed_keys.add(key_mapping[key])
            elif len(key) == 1 and key.isalpha():
                # For letter keys, store as lowercase character
                parsed_keys.add(key.lower())
            elif len(key) == 1:
                # For other single characters (numbers, symbols)
                parsed_keys.add(key)
            else:
                # Handle special keys like 'space', 'enter', etc.
                try:
                    parsed_keys.add(getattr(Key, key))
                except AttributeError:
                    print(f"Warning: Unknown key '{key}' in trigger combination")
        
        return parsed_keys
    
    def get_clipboard_content(self) -> str:
        """Get content from clipboard."""
        try:
            content = pyperclip.paste()
            return content
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return ""
    
    def type_content(self, content: str) -> None:
        """Type content using the most reliable method for the current platform."""
        if not content:
            print("Clipboard is empty or could not be read.")
            return
        
        print(f"Starting to type {len(content)} characters...")
        print("Press Ctrl+C to stop typing.")
        
        # Small delay before starting to type
        time.sleep(0.5)
        
        try:
            if self.windows_mode:
                # Use clipboard-based approach for Windows mode (most reliable)
                self._type_content_clipboard(content)
            else:
                # Use macOS-specific character-by-character typing with proper key combinations
                self._type_content_traditional(content)
                
        except KeyboardInterrupt:
            print("\n✗ Typing interrupted by user.")
        except Exception as e:
            print(f"\n✗ Error during typing: {e}")
            # Fallback to Unicode typing if primary method fails
            try:
                print("Trying fallback method...")
                self._type_content_unicode_fallback(content)
            except Exception as fallback_error:
                print(f"✗ Fallback method also failed: {fallback_error}")
    
    def _type_content_clipboard(self, content: str) -> None:
        """Type content using clipboard + Ctrl+V method (most reliable for Windows virtual desktop)."""
        if self.debug:
            print("[DEBUG] Using clipboard-based input method")
        
        try:
            # Store original clipboard content
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass  # Ignore if clipboard is empty or inaccessible
            
            # Set our content to clipboard
            pyperclip.copy(content)
            
            # Short delay to ensure clipboard is set
            time.sleep(0.1)
            
            # Send Cmd+V to paste (macOS)
            if self.debug:
                print("[DEBUG] Sending Cmd+V to paste content")
            
            pyautogui.hotkey('cmd', 'v')
            
            # Wait for paste to complete
            time.sleep(0.2)
            
            # Restore original clipboard content
            try:
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
            except:
                pass  # Ignore if restoration fails
            
            print(f"✓ Successfully pasted {len(content)} characters using clipboard method!")
            
        except Exception as e:
            print(f"✗ Clipboard method failed: {e}")
            raise  # Re-raise to trigger fallback
    
    def _type_character_macos(self, char: str) -> bool:
        """Type a single character using PyAutoGUI for macOS.
        
        Args:
            char: The character to type
            
        Returns:
            bool: True if character was typed successfully, False otherwise
        """
        try:
            # Check if we have a mapping for this character
            if char in MACOS_KEY_MAPPING:
                base_key, modifiers = MACOS_KEY_MAPPING[char]
                
                if self.debug:
                    modifier_names = [str(mod).split('.')[-1] for mod in modifiers]
                    print(f"[DEBUG] Typing '{char}' using mapping: {base_key} + {modifier_names if modifier_names else 'none'}")
                
                if Key.shift in modifiers:
                    # Use PyAutoGUI hotkey for shift combinations
                    try:
                        pyautogui.hotkey('shift', base_key)
                        if self.debug:
                            print(f"[DEBUG] Successfully typed '{char}' using PyAutoGUI hotkey")
                        return True
                    except Exception as e:
                        if self.debug:
                            print(f"[DEBUG] PyAutoGUI hotkey failed for '{char}': {e}")
                        return False
                elif modifiers:
                    # Handle other modifiers (not implemented yet, but structure ready)
                    if self.debug:
                        print(f"[DEBUG] Other modifier combinations not yet implemented")
                    return False
                else:
                    # No modifiers needed, just press the base key
                    try:
                        pyautogui.press(base_key)
                        if self.debug:
                            print(f"[DEBUG] Successfully typed base key '{base_key}' using PyAutoGUI")
                        return True
                    except Exception as e:
                        if self.debug:
                            print(f"[DEBUG] PyAutoGUI press failed for '{base_key}': {e}")
                        return False
                
            else:
                # Character not in mapping - NO FALLBACK, return False
                if self.debug:
                    print(f"[DEBUG] Character '{char}' not in mapping - no fallback, skipping")
                return False
                
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Failed to type character '{char}': {e}")
            return False
    
    
    def _type_content_unicode_fallback(self, content: str) -> None:
        """Fallback method using PyAutoGUI write function."""
        if self.debug:
            print("[DEBUG] Using PyAutoGUI write fallback method")
        
        try:
            # Use PyAutoGUI write function as fallback
            pyautogui.write(content, interval=self.delay)
            
            print(f"✓ Successfully typed {len(content)} characters using PyAutoGUI write method!")
            
        except Exception as e:
            print(f"✗ PyAutoGUI write fallback method failed: {e}")
            raise
    
    def _type_content_macos(self, content: str) -> None:
        """macOS-optimized typing that avoids system interference while handling IDE auto-indentation."""
        if self.debug:
            print("[DEBUG] Using smart typing method with IDE auto-indent handling")
        
        # Check if content has multiple lines (likely code that needs smart indentation)
        if '\n' in content and any(line.startswith('    ') or line.startswith('\t') for line in content.split('\n')):
            if self.debug:
                print("[DEBUG] Multi-line content with indentation detected, using smart line-by-line method")
            self._type_content_smart_lines(content)
        else:
            if self.debug:
                print("[DEBUG] Simple content, using direct write method")
            try:
                # Use PyAutoGUI write method for simple content
                pyautogui.write(content, interval=self.delay)
                print(f"✓ Successfully typed {len(content)} characters using PyAutoGUI write method!")
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] PyAutoGUI write failed: {e}, falling back to unicode fallback")
                self._type_content_unicode_fallback(content)
    
    def _type_content_with_smart_timing(self, content: str) -> None:
        """Type content with smart timing that works with IDE auto-indentation without navigation keys."""
        if self.debug:
            print("[DEBUG] Using smart timing method - no navigation keys, just intelligent delays")
        
        try:
            # Pre-process content to work with IDE auto-indentation
            processed_content = self._preprocess_for_ide_indentation(content)
            
            if self.debug:
                print(f"[DEBUG] Pre-processed content to work with IDE auto-indentation")
                print(f"[DEBUG] Original lines: {len(content.split('\\n'))}, Processed lines: {len(processed_content.split('\\n'))}")
            
            # Use write with smart interval timing
            # Slightly longer delay for newlines to let IDE auto-indent settle
            if self.debug:
                print(f"[DEBUG] Typing {len(processed_content)} characters with smart timing")
            
            # Type character by character with smart delays
            for i, char in enumerate(processed_content):
                pyautogui.write(char)
                
                if char == '\n':
                    # Longer delay after newlines to let IDE auto-indent settle
                    time.sleep(self.delay * 3)
                else:
                    # Normal delay for other characters
                    time.sleep(self.delay)
                
                # Progress reporting
                if (i + 1) % 100 == 0:
                    print(f"Progress: {i + 1}/{len(processed_content)} characters typed")
            
            print(f"✓ Successfully typed {len(processed_content)} characters using smart timing method!")
            
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Smart timing method failed: {e}, falling back to basic write")
            # Final fallback to basic write
            pyautogui.write(content, interval=self.delay)
            print(f"✓ Successfully typed {len(content)} characters using fallback write method!")
    
    def _preprocess_for_ide_indentation(self, content: str) -> str:
        """Simple IDE-aware preprocessing: retain original indentation but account for IDE auto-indent on next line."""
        lines = content.split('\n')
        processed_lines = []
        
        if self.debug:
            print(f"[DEBUG] Simple IDE-aware preprocessing for {len(lines)} lines")
        
        for i, line in enumerate(lines):
            if i == 0:
                # Keep first line exactly as-is
                processed_lines.append(line)
                if self.debug:
                    print(f"[DEBUG] Line 1: Keep as-is: '{line[:30]}...'")
            else:
                # Check if previous line ends with ':' (triggers IDE auto-indent)
                previous_line = lines[i-1] if i > 0 else ""
                ide_will_auto_indent = previous_line.strip().endswith(':')
                
                if line.strip():  # Non-empty line
                    # Get original indentation
                    leading_spaces = len(line) - len(line.lstrip())
                    content_part = line.lstrip()
                    
                    if ide_will_auto_indent and leading_spaces >= 4:
                        # IDE will add 4 spaces, so subtract 4 from original
                        adjusted_spaces = leading_spaces - 4
                        adjusted_indent = ' ' * adjusted_spaces
                        processed_line = adjusted_indent + content_part
                        
                        if self.debug:
                            print(f"[DEBUG] Line {i+1}: IDE auto-indent, {leading_spaces}→{adjusted_spaces} spaces: '{processed_line[:30]}...'")
                    else:
                        # No IDE auto-indent expected, keep original
                        processed_line = line
                        
                        if self.debug:
                            print(f"[DEBUG] Line {i+1}: No auto-indent, keep original: '{line[:30]}...'")
                    
                    processed_lines.append(processed_line)
                else:
                    # Empty line - keep as empty
                    processed_lines.append('')
                    if self.debug:
                        print(f"[DEBUG] Line {i+1}: Empty line")
        
        result = '\n'.join(processed_lines)
        
        if self.debug:
            print(f"[DEBUG] Simple IDE-aware preprocessing completed")
            print(f"[DEBUG] Sample transformation:")
            for i in range(min(3, len(lines))):
                orig = repr(lines[i][:40] + ('...' if len(lines[i]) > 40 else ''))
                proc = repr(result.split('\n')[i][:40] + ('...' if len(result.split('\n')[i]) > 40 else ''))
                print(f"[DEBUG]   {i+1}: {orig} → {proc}")
        
        return result
    
    def _type_content_smart_lines(self, content: str) -> None:
        """Hybrid approach: pynput for indentation handling, PyAutoGUI for content typing."""
        if self.debug:
            print("[DEBUG] Using hybrid approach - pynput for indentation, PyAutoGUI for content")
        
        lines = content.split('\n')
        total_chars = 0
        
        for line_num, line in enumerate(lines):
            if line_num > 0:
                # Press Enter to go to new line (use PyAutoGUI for this)
                pyautogui.press('enter')
                total_chars += 1
                
                if self.delay > 0:
                    time.sleep(self.delay)
                
                # Handle indentation using original working pynput method
                leading_whitespace = len(line) - len(line.lstrip())
                if leading_whitespace > 0:
                    if self.debug:
                        print(f"[DEBUG] Line {line_num + 1}: Handling {leading_whitespace} spaces indentation with pynput")
                    
                    # Use pynput for navigation (proven working method)
                    self.keyboard_controller.press(Key.home)
                    self.keyboard_controller.release(Key.home)
                    
                    if self.delay > 0:
                        time.sleep(self.delay * 2)
                    
                    # Recreate exact indentation using pynput
                    for i in range(leading_whitespace):
                        if i < len(line) and line[i] == '\t':
                            self.keyboard_controller.press(Key.tab)
                            self.keyboard_controller.release(Key.tab)
                        else:
                            self.keyboard_controller.type(' ')
                        
                        if self.delay > 0:
                            time.sleep(self.delay)
                    
                    total_chars += leading_whitespace
                    
                    # Type content part using PyAutoGUI (interference-free)
                    content_part = line.lstrip()
                    if content_part:
                        if self.debug:
                            print(f"[DEBUG] Line {line_num + 1}: Typing content with PyAutoGUI: '{content_part[:40]}...'")
                        
                        pyautogui.write(content_part, interval=self.delay)
                        total_chars += len(content_part)
                else:
                    # No indentation, type whole line with PyAutoGUI
                    if line.strip():
                        if self.debug:
                            print(f"[DEBUG] Line {line_num + 1}: No indentation, typing with PyAutoGUI: '{line[:40]}...'")
                        
                        pyautogui.write(line, interval=self.delay)
                        total_chars += len(line)
            else:
                # First line - use PyAutoGUI
                if self.debug:
                    print(f"[DEBUG] Line 1: Typing with PyAutoGUI: '{line[:40]}...'")
                
                pyautogui.write(line, interval=self.delay)
                total_chars += len(line)
            
            # Print progress every 100 characters
            if total_chars % 100 == 0:
                print(f"Progress: {total_chars}/{len(content)} characters typed")
        
        print(f"✓ Successfully typed {len(content)} characters with hybrid approach!")
    
    def _type_content_character_fallback(self, content: str) -> None:
        """Fallback character-by-character typing for content that pyautogui.write() can't handle."""
        if self.debug:
            print("[DEBUG] Using character-by-character fallback method")
        
        lines = content.split('\n')
        total_chars = 0
        
        for line_num, line in enumerate(lines):
            if line_num > 0:
                # Press Enter to go to new line
                pyautogui.press('enter')
                total_chars += 1
                
                if self.delay > 0:
                    time.sleep(self.delay)
            
            # Type the line content
            for char in line:
                if char == '\t':
                    pyautogui.press('tab')
                else:
                    # Use individual key press/release to avoid hotkey conflicts
                    success = self._type_character_safe(char)
                    if not success:
                        if self.debug:
                            print(f"[DEBUG] Could not type character '{char}', skipping")
                        continue
                
                # Add delay between keystrokes
                if self.delay > 0:
                    time.sleep(self.delay)
                
                total_chars += 1
                
                # Print progress every 100 characters
                if total_chars % 100 == 0:
                    print(f"Progress: {total_chars}/{len(content)} characters typed")
        
        print(f"✓ Successfully typed {len(content)} characters using character fallback method!")
    
    def _type_character_safe(self, char: str) -> bool:
        """Type a single character using safer key press/release method."""
        try:
            # Check if we have a mapping for this character
            if char in MACOS_KEY_MAPPING:
                base_key, modifiers = MACOS_KEY_MAPPING[char]
                
                if self.debug:
                    modifier_names = [str(mod).split('.')[-1] for mod in modifiers]
                    print(f"[DEBUG] Typing '{char}' using safe method: {base_key} + {modifier_names if modifier_names else 'none'}")
                
                if Key.shift in modifiers:
                    # Use individual key press/release instead of hotkey to avoid conflicts
                    try:
                        pyautogui.keyDown('shift')
                        time.sleep(0.01)  # Small delay
                        pyautogui.press(base_key)
                        time.sleep(0.01)  # Small delay
                        pyautogui.keyUp('shift')
                        
                        if self.debug:
                            print(f"[DEBUG] Successfully typed '{char}' using safe shift method")
                        return True
                    except Exception as e:
                        if self.debug:
                            print(f"[DEBUG] Safe shift method failed for '{char}': {e}")
                        return False
                else:
                    # No modifiers needed, just press the base key
                    try:
                        pyautogui.press(base_key)
                        if self.debug:
                            print(f"[DEBUG] Successfully typed base key '{base_key}' using safe method")
                        return True
                    except Exception as e:
                        if self.debug:
                            print(f"[DEBUG] Safe press failed for '{base_key}': {e}")
                        return False
                
            else:
                # Character not in mapping - try pyautogui.write for single character
                try:
                    pyautogui.write(char)
                    return True
                except Exception as e:
                    if self.debug:
                        print(f"[DEBUG] Character '{char}' not in mapping and write failed: {e}")
                    return False
                
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Failed to type character '{char}': {e}")
            return False
    
    def _type_content_traditional(self, content: str) -> None:
        """Traditional character-by-character typing for Mac mode (deprecated)."""
        # Keep the old method for backward compatibility, but use the new macOS method
        self._type_content_macos(content)
    
    def on_key_press(self, key):
        """Handle key press events."""
        try:
            # Convert character keys to lowercase for consistent matching
            if hasattr(key, 'char') and key.char:
                processed_key = key.char.lower()
            else:
                processed_key = key
                
            self.pressed_keys.add(processed_key)
            
            # Debug: Print key press (uncomment for debugging)
            # print(f"Key pressed: {processed_key} | Currently pressed: {self.pressed_keys}")
            
            # Check if trigger combination is pressed
            if self.trigger_keys.issubset(self.pressed_keys):
                print(f"\n🚀 Trigger activated! Reading clipboard and typing content...")
                # Run typing in a separate thread to avoid blocking the listener
                threading.Thread(target=self._handle_trigger, daemon=True).start()
                
        except UnicodeDecodeError:
            # Handle macOS pynput Unicode decode issues for special characters
            # This is common on macOS and shouldn't cause the app to exit
            pass
        except AttributeError:
            # Handle cases where key might not have expected attributes
            # This can happen with certain special keys on macOS
            pass
    
    def on_key_release(self, key):
        """Handle key release events."""
        try:
            # Convert character keys to lowercase for consistent matching
            if hasattr(key, 'char') and key.char:
                processed_key = key.char.lower()
            else:
                processed_key = key
                
            # Remove key from pressed keys set
            self.pressed_keys.discard(processed_key)
            
            # Debug: Print key release (uncomment for debugging)
            # print(f"Key released: {processed_key} | Currently pressed: {self.pressed_keys}")
            
            # Exit ONLY on actual Escape key - be very specific
            if key == Key.esc:
                print("\n👋 Exiting ProKeys...")
                return False
                
        except UnicodeDecodeError:
            # Handle macOS pynput Unicode decode issues for special characters
            # Only check for Escape if we can actually identify the key
            try:
                if key == Key.esc:
                    print("\n👋 Exiting ProKeys...")
                    return False
            except:
                # If we can't even check for Escape, just continue
                pass
        except AttributeError:
            # Handle cases where key might not have expected attributes
            # This can happen with certain special keys on macOS
            pass
    
    def _handle_trigger(self):
        """Handle the trigger key combination."""
        content = self.get_clipboard_content()
        if content:
            # Clear pressed keys to avoid interference
            self.pressed_keys.clear()
            self.type_content(content)
        else:
            print("No content found in clipboard.")
    
    def start_listening(self):
        """Start listening for key combinations."""
        print("🎯 ProKeys is now running in background!")
        print(f"📋 Trigger: {self.trigger_key}")
        print(f"⏱️  Delay: {self.delay}s between keystrokes")
        print("🔥 Copy anything, then press the trigger combination to paste with formatting")
        print("🚪 Press Escape to exit")
        print("-" * 50)
        
        self.running = True
        
        with Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        ) as listener:
            self.listener = listener
            listener.join()
    
    def test_character_mapping(self):
        """Test the character mapping to ensure all common characters are supported."""
        print("🧪 Testing macOS character mapping...")
        
        # Test cases with different character types
        test_cases = [
            ("Hello World!", "Basic text with exclamation"),
            ("user@example.com", "Email with @ symbol"),
            ("Price: $19.99", "Text with dollar sign"),
            ("Code: if (x > 0) { return true; }", "Programming syntax"),
            ("Math: 50% + 25% = 75%", "Percentage symbols"),
            ("Special: !@#$%^&*()", "All shift number symbols"),
            ("Mixed: ABC123def", "Mixed case and numbers"),
            ("Quotes: 'Hello' and \"World\"", "Single and double quotes"),
            ("Brackets: [array] {object} (group)", "Various brackets"),
            ("Symbols: <tag> file.txt & more|less", "Mixed symbols"),
        ]
        
        total_chars = 0
        supported_chars = 0
        unsupported_chars = []
        
        for test_text, description in test_cases:
            print(f"  Testing: {description}")
            for char in test_text:
                total_chars += 1
                if char in MACOS_KEY_MAPPING:
                    supported_chars += 1
                    base_key, modifiers = MACOS_KEY_MAPPING[char]
                    modifier_names = [str(mod).split('.')[-1] for mod in modifiers]
                    if self.debug:
                        print(f"    '{char}' -> {base_key} + {modifier_names if modifier_names else 'none'}")
                else:
                    if char not in unsupported_chars and char not in ['\n', '\t']:
                        unsupported_chars.append(char)
        
        coverage = (supported_chars / total_chars) * 100
        print(f"\n📊 Character Mapping Coverage:")
        print(f"  Total characters tested: {total_chars}")
        print(f"  Supported by mapping: {supported_chars}")
        print(f"  Coverage: {coverage:.1f}%")
        
        if unsupported_chars:
            print(f"  ⚠️  Unsupported characters (will use fallback): {unsupported_chars}")
        else:
            print(f"  ✅ All test characters are supported!")
        
        # Test specific shift combinations
        print(f"\n🔢 Testing shift number combinations:")
        shift_tests = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
            '6': '^', '7': '&', '8': '*', '9': '(', '0': ')'
        }
        
        for base, expected in shift_tests.items():
            if expected in MACOS_KEY_MAPPING:
                mapped_base, modifiers = MACOS_KEY_MAPPING[expected]
                shift_used = Key.shift in modifiers
                correct_base = mapped_base == base
                if shift_used and correct_base:
                    print(f"  ✅ {base} + Shift = {expected}")
                else:
                    print(f"  ❌ {base} + Shift = {expected} (mapping issue)")
            else:
                print(f"  ❌ {expected} not in mapping")
        
        print(f"\n✅ Character mapping test completed!")
        return coverage > 95  # Return True if coverage is good
    
    def paste_once(self):
        """Paste clipboard content once and exit."""
        print("🎯 ProKeys - One-time paste mode")
        content = self.get_clipboard_content()
        self.type_content(content)


def main():
    # Check if config subcommand is used
    if len(sys.argv) > 1 and sys.argv[1] == "config":
        interactive_config()
        return
    
    # Load configuration
    config = load_config()
    
    parser = argparse.ArgumentParser(
        description="ProKeys - Clipboard Content Keystroke Emulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    python prokeys.py                          # Start with config settings ({config['typing_speed_wpm']} WPM)
    python prokeys.py config                   # Configure typing speed (9-999 WPM)
    python prokeys.py --delay 0.02             # Override delay (slower typing)
    python prokeys.py --trigger-key "ctrl+alt+v"  # Custom trigger key
    python prokeys.py --once                    # Paste once and exit

Configuration:
    Current: {config['typing_speed_wpm']} WPM, Delay: {config['delay']:.4f}s
    Use 'python prokeys.py config' to change typing speed
        """
    )
    
    parser.add_argument(
        '--delay', 
        type=float, 
        default=config['delay'],
        help=f'Delay between keystrokes in seconds (config: {config["delay"]:.4f}s)'
    )
    
    parser.add_argument(
        '--trigger-key',
        type=str,
        default=config['trigger_key'],
        help=f'Key combination to trigger pasting (config: {config["trigger_key"]})'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Paste clipboard content once and exit (no hotkey listening)'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current configuration and exit'
    )
    
    parser.add_argument(
        '--windows-mode',
        action='store_true',
        default=config.get('windows_mode', False),
        help=f'Use Windows keyboard layout mode (config: {config.get("windows_mode", False)})'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode to see what keys are being sent'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the macOS character mapping and exit'
    )
    
    
    args = parser.parse_args()
    
    # Show config if requested
    if args.show_config:
        show_config()
        return
    
    # Run character mapping test if requested
    if args.test:
        print("🧪 Running macOS character mapping test...")
        test_prokeys = ProKeys(delay=0.01, debug=args.debug)
        success = test_prokeys.test_character_mapping()
        if success:
            print("\n✅ All tests passed! macOS character mapping is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️  Some issues found in character mapping. See details above.")
            sys.exit(1)
    
    # Validate delay
    if args.delay < 0:
        print("Error: Delay cannot be negative")
        sys.exit(1)
    
    # Show current settings
    delay_to_wpm = 12.0 / args.delay if args.delay > 0 else 999
    print(f"⚡ ProKeys starting with {delay_to_wpm:.0f} WPM (delay: {args.delay:.4f}s)")
    if args.windows_mode:
        print(f"🪟 Windows mode enabled - using clipboard-based input for maximum compatibility")
    if args.debug:
        print("🐛 Debug mode enabled - will show input method details")
    
    try:
        prokeys = ProKeys(delay=args.delay, trigger_key=args.trigger_key, windows_mode=args.windows_mode, debug=args.debug)
        
        if args.once:
            prokeys.paste_once()
        else:
            prokeys.start_listening()
            
    except KeyboardInterrupt:
        print("\n👋 ProKeys terminated by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
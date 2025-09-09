"""
Sample Mod Manager Dialog
GUI để quản lý các mod mẫu, chỉnh sửa và tạo version mới
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Dict, List, Optional, Callable
import threading
from datetime import datetime

from sample_mod_manager import SampleModManager, SampleModInfo, VersionType
from logger_config import get_logger


class SampleModDialog:
    """Dialog để quản lý sample mods"""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        self.parent = parent
        self.callback = callback  # Callback khi user chọn mod
        self.logger = get_logger("SampleModDialog")
        
        # Initialize managers
        self.sample_manager = SampleModManager()
        self.sample_mods: List[SampleModInfo] = []
        self.selected_mod: Optional[SampleModInfo] = None
        
        # Create dialog window
        self.create_dialog()
        self.load_sample_mods()
    
    def create_dialog(self):
        """Tạo dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🎮 Sample Mod Manager")
        self.dialog.geometry("900x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Create main layout
        self.create_widgets()
    
    def center_dialog(self):
        """Căn giữa dialog"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """Tạo các widgets"""
        main_frame = tk.Frame(self.dialog, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="📦 Sample Mod Manager", 
                              font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 10))
        
        # Create paned window
        paned = ttk.PanedWindow(main_frame, orient='horizontal')
        paned.pack(fill='both', expand=True)
        
        # Left panel - Mod list
        self.create_mod_list_panel(paned)
        
        # Right panel - Mod details và actions
        self.create_details_panel(paned)
        
        # Bottom buttons
        self.create_action_buttons(main_frame)
    
    def create_mod_list_panel(self, parent):
        """Tạo panel danh sách mods"""
        left_frame = tk.Frame(parent, bg='#f0f0f0')
        parent.add(left_frame, weight=1)
        
        # Header
        header_frame = tk.Frame(left_frame, bg='#f0f0f0')
        header_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(header_frame, text="📋 Available Sample Mods", 
                font=('Arial', 11, 'bold'), bg='#f0f0f0').pack(side='left')
        
        # Refresh button
        refresh_btn = tk.Button(header_frame, text="🔄", command=self.refresh_mods,
                               bg='#3498db', fg='white', font=('Arial', 8, 'bold'),
                               width=3, height=1)
        refresh_btn.pack(side='right')
        
        # Mod listbox with scrollbar
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill='both', expand=True)
        
        # Configure columns for treeview
        columns = ('version', 'modified')
        self.mod_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        
        # Configure column headings
        self.mod_tree.heading('#0', text='Mod Name', anchor='w')
        self.mod_tree.heading('version', text='Version', anchor='center')
        self.mod_tree.heading('modified', text='Modified', anchor='center')
        
        # Configure column widths
        self.mod_tree.column('#0', width=200, minwidth=150)
        self.mod_tree.column('version', width=80, minwidth=60)
        self.mod_tree.column('modified', width=100, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.mod_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient='horizontal', command=self.mod_tree.xview)
        self.mod_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.mod_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Bind selection event
        self.mod_tree.bind('<<TreeviewSelect>>', self.on_mod_select)
    
    def create_details_panel(self, parent):
        """Tạo panel chi tiết mod"""
        right_frame = tk.Frame(parent, bg='#f0f0f0')
        parent.add(right_frame, weight=1)
        
        # Header
        tk.Label(right_frame, text="📝 Mod Details & Actions", 
                font=('Arial', 11, 'bold'), bg='#f0f0f0').pack(pady=(0, 10))
        
        # Details frame
        details_frame = tk.LabelFrame(right_frame, text="ℹ️ Information", 
                                     font=('Arial', 10, 'bold'))
        details_frame.pack(fill='x', pady=(0, 10))
        
        # Create details labels
        self.detail_labels = {}
        detail_fields = [
            ('name', '📦 Name:'),
            ('version', '🏷️ Version:'),
            ('title', '🎯 Title:'),
            ('author', '👤 Author:'),
            ('factorio_version', '🎮 Factorio Version:'),
            ('locale_files_count', '🌍 Locale Files:')
        ]
        
        for field, label_text in detail_fields:
            row_frame = tk.Frame(details_frame)
            row_frame.pack(fill='x', padx=5, pady=2)
            
            tk.Label(row_frame, text=label_text, font=('Arial', 9, 'bold'), 
                    width=15, anchor='w').pack(side='left')
            
            value_label = tk.Label(row_frame, text='', font=('Arial', 9), 
                                 anchor='w', bg='white', relief='sunken', padx=5)
            value_label.pack(side='left', fill='x', expand=True, padx=(5, 0))
            
            self.detail_labels[field] = value_label
        
        # Description
        desc_frame = tk.LabelFrame(right_frame, text="📄 Description", 
                                  font=('Arial', 10, 'bold'))
        desc_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.desc_text = scrolledtext.ScrolledText(desc_frame, height=6, wrap='word',
                                                  font=('Arial', 9), state='disabled')
        self.desc_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Dependencies frame
        deps_frame = tk.LabelFrame(right_frame, text="🔗 Dependencies", 
                                  font=('Arial', 10, 'bold'))
        deps_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.deps_listbox = tk.Listbox(deps_frame, height=5, font=('Arial', 8))
        deps_scrollbar = tk.Scrollbar(deps_frame, orient='vertical')
        deps_scrollbar.config(command=self.deps_listbox.yview)
        self.deps_listbox.config(yscrollcommand=deps_scrollbar.set)
        
        self.deps_listbox.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        deps_scrollbar.pack(side='right', fill='y', pady=5)
    
    def create_action_buttons(self, parent):
        """Tạo action buttons"""
        button_frame = tk.Frame(parent, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(10, 0))
        
        # Action buttons
        actions = [
            ("📤 Load as Template", self.load_as_template, '#27ae60'),
            ("✏️ Create Enhanced Version", self.create_enhanced_version, '#e67e22'),
            ("🔧 Edit & New Version", self.edit_and_create_version, '#9b59b6'),
            ("❌ Close", self.close_dialog, '#95a5a6')
        ]
        
        for text, command, color in actions:
            btn = tk.Button(button_frame, text=text, command=command,
                           bg=color, fg='white', font=('Arial', 9, 'bold'),
                           padx=15, pady=5)
            btn.pack(side='left', padx=5)
    
    def load_sample_mods(self):
        """Load danh sách sample mods"""
        try:
            self.sample_mods = self.sample_manager.scan_sample_mods()
            self.populate_mod_list()
            self.logger.info(f"Loaded {len(self.sample_mods)} sample mods")
        except Exception as e:
            self.logger.error(f"Failed to load sample mods: {e}")
            messagebox.showerror("Error", f"Failed to load sample mods: {str(e)}")
    
    def populate_mod_list(self):
        """Populate mod list"""
        # Clear existing items
        for item in self.mod_tree.get_children():
            self.mod_tree.delete(item)
        
        # Add sample mods
        for i, mod in enumerate(self.sample_mods):
            # Format modified date
            modified_str = mod.last_modified.strftime("%m/%d/%Y") if mod.last_modified else "Unknown"
            
            # Insert into treeview
            item_id = self.mod_tree.insert('', 'end', 
                                          text=mod.title or mod.name,
                                          values=(mod.version, modified_str))
            
            # Store mod index as tag
            self.mod_tree.item(item_id, tags=(str(i),))
    
    def refresh_mods(self):
        """Refresh mod list"""
        self.load_sample_mods()
        messagebox.showinfo("Refresh", "Sample mod list refreshed!")
    
    def on_mod_select(self, event):
        """Handle mod selection"""
        selection = self.mod_tree.selection()
        if not selection:
            self.selected_mod = None
            self.clear_details()
            return
        
        item = selection[0]
        try:
            # Get mod index from tags
            tags = self.mod_tree.item(item)['tags']
            if tags:
                mod_index = int(tags[0])
                self.selected_mod = self.sample_mods[mod_index]
                self.display_mod_details(self.selected_mod)
            else:
                self.logger.warning("No mod index found in tags")
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error selecting mod: {e}")
    
    def display_mod_details(self, mod_info: SampleModInfo):
        """Hiển thị chi tiết mod"""
        # Update detail labels
        details = {
            'name': mod_info.name,
            'version': mod_info.version,
            'title': mod_info.title,
            'author': mod_info.author,
            'factorio_version': mod_info.factorio_version,
            'locale_files_count': f"{len(mod_info.locale_files)} files"
        }
        
        for field, value in details.items():
            if field in self.detail_labels:
                self.detail_labels[field].config(text=value or 'N/A')
        
        # Update description
        self.desc_text.config(state='normal')
        self.desc_text.delete('1.0', 'end')
        self.desc_text.insert('1.0', mod_info.description or 'No description available')
        self.desc_text.config(state='disabled')
        
        # Update dependencies
        self.deps_listbox.delete(0, 'end')
        for dep in mod_info.dependencies:
            self.deps_listbox.insert('end', dep)
    
    def clear_details(self):
        """Clear details panel"""
        for label in self.detail_labels.values():
            label.config(text='')
        
        self.desc_text.config(state='normal')
        self.desc_text.delete('1.0', 'end')
        self.desc_text.config(state='disabled')
        
        self.deps_listbox.delete(0, 'end')
    
    def load_as_template(self):
        """Load selected mod as template"""
        if not self.selected_mod:
            messagebox.showwarning("Warning", "Please select a mod first!")
            return
        
        try:
            # Load existing translations
            translations = self.sample_manager.load_sample_translations(self.selected_mod)
            
            if self.callback:
                # Call parent callback với mod info và translations
                self.callback({
                    'mod_info': self.selected_mod,
                    'translations': translations,
                    'action': 'load_template'
                })
            
            messagebox.showinfo("Success", 
                              f"Loaded {len(translations)} translation files from {self.selected_mod.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load template: {e}")
            messagebox.showerror("Error", f"Failed to load template: {str(e)}")
    
    def create_enhanced_version(self):
        """Tạo enhanced version của mod"""
        if not self.selected_mod:
            messagebox.showwarning("Warning", "Please select a mod first!")
            return
        
        # Show enhancement dialog
        self.show_enhancement_dialog()
    
    def edit_and_create_version(self):
        """Edit mod và tạo version mới"""
        if not self.selected_mod:
            messagebox.showwarning("Warning", "Please select a mod first!")
            return
        
        # Show edit dialog
        self.show_edit_dialog()
    
    def show_enhancement_dialog(self):
        """Show dialog để enhance mod"""
        EnhancementDialog(self.dialog, self.selected_mod, self.sample_manager, 
                         self.on_mod_created)
    
    def show_edit_dialog(self):
        """Show dialog để edit mod"""
        EditModDialog(self.dialog, self.selected_mod, self.sample_manager, 
                     self.on_mod_created)
    
    def on_mod_created(self, new_mod_path: str):
        """Callback khi mod mới được tạo"""
        messagebox.showinfo("Success", f"New mod created: {new_mod_path}")
        # Refresh mod list để show mod mới
        self.refresh_mods()
    
    def close_dialog(self):
        """Đóng dialog"""
        self.dialog.destroy()


class EnhancementDialog:
    """Dialog để enhance existing mod"""
    
    def __init__(self, parent, mod_info: SampleModInfo, 
                 sample_manager: SampleModManager, callback: Callable):
        self.parent = parent
        self.mod_info = mod_info
        self.sample_manager = sample_manager
        self.callback = callback
        self.logger = get_logger("EnhancementDialog")
        
        self.create_dialog()
    
    def create_dialog(self):
        """Tạo enhancement dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"🚀 Enhance Mod: {self.mod_info.name}")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        main_frame = tk.Frame(self.dialog, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Title
        title = tk.Label(main_frame, 
                        text=f"🚀 Enhance: {self.mod_info.title}", 
                        font=('Arial', 12, 'bold'), bg='#f0f0f0')
        title.pack(pady=(0, 15))
        
        # Version type selection
        version_frame = tk.LabelFrame(main_frame, text="📈 Version Update Type", 
                                    font=('Arial', 10, 'bold'))
        version_frame.pack(fill='x', pady=(0, 10))
        
        self.version_type_var = tk.StringVar(value="minor")
        version_types = [
            ("Major (1.0.0 → 2.0.0)", "major"),
            ("Minor (1.0.0 → 1.1.0)", "minor"), 
            ("Patch (1.0.0 → 1.0.1)", "patch")
        ]
        
        for text, value in version_types:
            tk.Radiobutton(version_frame, text=text, variable=self.version_type_var, 
                          value=value, bg='#f0f0f0', font=('Arial', 9)).pack(anchor='w', padx=10, pady=2)
        
        # New dependencies
        deps_frame = tk.LabelFrame(main_frame, text="🔗 Add New Dependencies", 
                                 font=('Arial', 10, 'bold'))
        deps_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        tk.Label(deps_frame, text="Enter new dependencies (one per line):", 
                font=('Arial', 9)).pack(anchor='w', padx=5, pady=(5, 0))
        
        self.deps_text = scrolledtext.ScrolledText(deps_frame, height=6, wrap='word',
                                                  font=('Arial', 9))
        self.deps_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(button_frame, text="🚀 Create Enhanced Mod", 
                 command=self.create_enhanced, bg='#27ae60', fg='white',
                 font=('Arial', 10, 'bold'), padx=20).pack(side='left')
        
        tk.Button(button_frame, text="❌ Cancel", 
                 command=self.dialog.destroy, bg='#e74c3c', fg='white',
                 font=('Arial', 10, 'bold'), padx=20).pack(side='right')
    
    def create_enhanced(self):
        """Tạo enhanced mod"""
        try:
            # Get version type
            version_type = VersionType(self.version_type_var.get())
            
            # Get new dependencies
            deps_text = self.deps_text.get('1.0', 'end').strip()
            new_deps = [dep.strip() for dep in deps_text.split('\n') if dep.strip()]
            
            # Create enhanced mod
            new_mod_path = self.sample_manager.create_enhanced_mod(
                self.mod_info,
                new_dependencies=new_deps if new_deps else None,
                version_type=version_type
            )
            
            self.callback(new_mod_path)
            self.dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to create enhanced mod: {e}")
            messagebox.showerror("Error", f"Failed to create enhanced mod: {str(e)}")


class EditModDialog:
    """Dialog để edit mod chi tiết"""
    
    def __init__(self, parent, mod_info: SampleModInfo, 
                 sample_manager: SampleModManager, callback: Callable):
        self.parent = parent
        self.mod_info = mod_info
        self.sample_manager = sample_manager
        self.callback = callback
        self.logger = get_logger("EditModDialog")
        
        self.create_dialog()
    
    def create_dialog(self):
        """Tạo edit dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"✏️ Edit Mod: {self.mod_info.name}")
        self.dialog.geometry("700x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        main_frame = tk.Frame(self.dialog, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Basic info tab
        self.create_basic_info_tab(notebook)
        
        # Locale files tab
        self.create_locale_tab(notebook)
        
        # Dependencies tab
        self.create_dependencies_tab(notebook)
        
        # Action buttons
        self.create_action_buttons(main_frame)
    
    def create_basic_info_tab(self, parent):
        """Tạo tab basic info"""
        basic_frame = tk.Frame(parent, bg='#f0f0f0')
        parent.add(basic_frame, text="📝 Basic Info")
        
        # Create entry fields
        self.basic_vars = {}
        basic_fields = [
            ('title', 'Title:'),
            ('author', 'Author:'),
            ('description', 'Description:'),
            ('factorio_version', 'Factorio Version:')
        ]
        
        for field, label_text in basic_fields:
            row_frame = tk.Frame(basic_frame, bg='#f0f0f0')
            row_frame.pack(fill='x', padx=10, pady=5)
            
            tk.Label(row_frame, text=label_text, font=('Arial', 10, 'bold'),
                    width=15, anchor='w', bg='#f0f0f0').pack(side='left')
            
            if field == 'description':
                # Multi-line text for description
                var = tk.StringVar(value=getattr(self.mod_info, field, ''))
                text_widget = scrolledtext.ScrolledText(row_frame, height=4, wrap='word',
                                                       font=('Arial', 9))
                text_widget.insert('1.0', getattr(self.mod_info, field, ''))
                text_widget.pack(side='left', fill='both', expand=True, padx=(5, 0))
                self.basic_vars[field] = text_widget
            else:
                # Single line entry
                var = tk.StringVar(value=getattr(self.mod_info, field, ''))
                entry = tk.Entry(row_frame, textvariable=var, font=('Arial', 9))
                entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
                self.basic_vars[field] = var
    
    def create_locale_tab(self, parent):
        """Tạo tab locale files"""
        locale_frame = tk.Frame(parent, bg='#f0f0f0')
        parent.add(locale_frame, text="🌍 Locale Files")
        
        tk.Label(locale_frame, text="Add new locale file content (filename.cfg):",
                font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w', padx=10, pady=(10, 5))
        
        # Filename entry
        filename_frame = tk.Frame(locale_frame, bg='#f0f0f0')
        filename_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(filename_frame, text="Filename:", font=('Arial', 9, 'bold'),
                bg='#f0f0f0').pack(side='left')
        
        self.filename_var = tk.StringVar()
        filename_entry = tk.Entry(filename_frame, textvariable=self.filename_var, 
                                font=('Arial', 9))
        filename_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        # Content text area
        tk.Label(locale_frame, text="Content:", font=('Arial', 9, 'bold'),
                bg='#f0f0f0').pack(anchor='w', padx=10, pady=(10, 0))
        
        self.locale_content_text = scrolledtext.ScrolledText(locale_frame, height=15, 
                                                           wrap='word', font=('Courier', 9))
        self.locale_content_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Sample content
        sample_content = """[entity-name]
sample-entity=Sample Entity
another-entity=Another Entity

[item-name]  
sample-item=Sample Item
"""
        self.locale_content_text.insert('1.0', sample_content)
    
    def create_dependencies_tab(self, parent):
        """Tạo tab dependencies"""
        deps_frame = tk.Frame(parent, bg='#f0f0f0')
        parent.add(deps_frame, text="🔗 Dependencies")
        
        tk.Label(deps_frame, text="Dependencies (one per line):",
                font=('Arial', 10, 'bold'), bg='#f0f0f0').pack(anchor='w', padx=10, pady=(10, 5))
        
        self.deps_text = scrolledtext.ScrolledText(deps_frame, height=20, wrap='word',
                                                  font=('Arial', 9))
        self.deps_text.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Load existing dependencies
        existing_deps = '\n'.join(self.mod_info.dependencies)
        self.deps_text.insert('1.0', existing_deps)
    
    def create_action_buttons(self, parent):
        """Tạo action buttons"""
        button_frame = tk.Frame(parent, bg='#f0f0f0')
        button_frame.pack(fill='x', pady=(15, 0))
        
        # Version type selection
        version_frame = tk.Frame(button_frame, bg='#f0f0f0')
        version_frame.pack(side='left')
        
        tk.Label(version_frame, text="Version:", font=('Arial', 9, 'bold'),
                bg='#f0f0f0').pack(side='left')
        
        self.version_type_var = tk.StringVar(value="minor")
        version_combo = ttk.Combobox(version_frame, textvariable=self.version_type_var,
                                   values=["major", "minor", "patch"], width=8)
        version_combo.pack(side='left', padx=(5, 10))
        
        # Action buttons
        tk.Button(button_frame, text="✅ Create New Version", 
                 command=self.create_new_version, bg='#27ae60', fg='white',
                 font=('Arial', 10, 'bold'), padx=20).pack(side='left', padx=5)
        
        tk.Button(button_frame, text="❌ Cancel", 
                 command=self.dialog.destroy, bg='#e74c3c', fg='white',
                 font=('Arial', 10, 'bold'), padx=20).pack(side='right')
    
    def create_new_version(self):
        """Tạo version mới của mod"""
        try:
            # Collect updates from basic info
            updates = {}
            
            for field, widget in self.basic_vars.items():
                if field == 'description':
                    # Text widget
                    value = widget.get('1.0', 'end').strip()
                else:
                    # StringVar
                    value = widget.get().strip()
                
                if value and value != getattr(self.mod_info, field, ''):
                    updates[field] = value
            
            # Get dependencies
            deps_text = self.deps_text.get('1.0', 'end').strip()
            new_deps = [dep.strip() for dep in deps_text.split('\n') if dep.strip()]
            if new_deps != self.mod_info.dependencies:
                updates['dependencies'] = new_deps
            
            # Get locale file content
            new_locale_files = {}
            filename = self.filename_var.get().strip()
            content = self.locale_content_text.get('1.0', 'end').strip()
            
            if filename and content:
                if not filename.endswith('.cfg'):
                    filename += '.cfg'
                new_locale_files[filename] = content
            
            # Get version type
            version_type = VersionType(self.version_type_var.get())
            
            # Create new version
            new_mod_path = self.sample_manager.mod_editor.create_new_mod_version(
                self.mod_info.zip_path,
                updates,
                new_locale_files if new_locale_files else None,
                version_type
            )
            
            self.callback(new_mod_path)
            self.dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to create new version: {e}")
            messagebox.showerror("Error", f"Failed to create new version: {str(e)}")


# Convenience function để mở sample mod dialog
def show_sample_mod_dialog(parent, callback=None):
    """Show sample mod dialog"""
    return SampleModDialog(parent, callback)

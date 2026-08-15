import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from hadocs.gui.config_persistence import try_config_callback, try_save_config
from hadocs.gui.theme import Theme
from hadocs.utils.config import save_config

class SettingsDialog(tk.Toplevel):

    def __init__(self, master, cfg, on_save):
        super().__init__(master)
        self.title("HADocs Settings")
        self.geometry("760x720")
        self.transient(master)
        Theme.apply(self)

        self.cfg = dict(cfg)
        self.on_save = on_save

        try:
            from hadocs.security.credential_store import get_home_assistant_token
            stored_token = get_home_assistant_token() or ""
        except Exception:
            stored_token = ""

        self.url_var = tk.StringVar(value=self.cfg.get("ha_url", ""))
        self.token_var = tk.StringVar(value=stored_token or self.cfg.get("token", ""))
        self.project_var = tk.StringVar(value=self.cfg.get("project_name", "My Smart Home"))
        self.output_var = tk.StringVar(value=self.cfg.get("output_dir", "output"))
        self.auto_open_var = tk.BooleanVar(value=bool(self.cfg.get("open_dashboard_after_scan", True)))
        self.database_enabled_var = tk.BooleanVar(
            value=bool(self.cfg.get("hask_database_enabled", False))
        )
        self.database_path_var = tk.StringVar(
            value=str(self.cfg.get("hask_database_path", ""))
        )
        self.installation_ref_var = tk.StringVar(
            value=str(self.cfg.get("hask_database_installation_ref", ""))
        )
        self.hask_enabled_var = tk.BooleanVar(
            value=bool(self.cfg.get("hask_enabled", False))
        )
        self.hask_preview_enabled_var = tk.BooleanVar(
            value=bool(self.cfg.get("hask_preview_enabled", False))
        )
        self.candidate_enabled_var = tk.BooleanVar(
            value=bool(self.cfg.get("hask_candidate_evidence_enabled", False))
        )
        self.native_status_enabled_var = tk.BooleanVar(
            value=bool(self.cfg.get("hask_native_integration_status_enabled", False))
        )
        self.database_status_var = tk.StringVar(value="Status not yet available")

        frame = ttk.Frame(self, style="Panel.TFrame", padding=22)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Settings", style="Hero.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 22))

        rows = [
            ("Home Assistant URL", self.url_var, False),
            ("Home Assistant Token", self.token_var, True),
            ("Project name", self.project_var, False),
            ("Output folder", self.output_var, False),
        ]

        for idx, (label, var, secret) in enumerate(rows, start=1):
            ttk.Label(frame, text=label, style="Panel.TLabel").grid(row=idx, column=0, sticky="w", padx=(0, 12), pady=7)
            ttk.Entry(frame, textvariable=var, show="*" if secret else "").grid(row=idx, column=1, sticky="ew", pady=7)

        self.token_status = ttk.Label(
            frame,
            text="🔒 Stored in Windows Credential Manager" if stored_token else "Token will be stored securely in Windows",
            style="MutedPanel.TLabel",
        )
        self.token_status.grid(row=2, column=2, sticky="w", padx=(12, 0), pady=7)

        ttk.Button(frame, text="Forget token", command=self.forget_token).grid(row=5, column=1, sticky="w", pady=(8, 0))

        ttk.Checkbutton(frame, text="Open dashboard after scan", variable=self.auto_open_var).grid(row=6, column=0, columnspan=3, sticky="w", pady=(20, 4))

        database = ttk.LabelFrame(
            frame, text="Operational database", padding=12
        )
        database.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(18, 0))
        database.columnconfigure(1, weight=1)

        ttk.Label(database, textvariable=self.database_status_var).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )
        ttk.Checkbutton(
            database,
            text="Enable operational database persistence",
            variable=self.database_enabled_var,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=3)
        ttk.Label(database, text="Database path").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=3
        )
        ttk.Entry(database, textvariable=self.database_path_var).grid(
            row=2, column=1, sticky="ew", pady=3
        )
        ttk.Button(database, text="Browse...", command=self.browse_database).grid(
            row=2, column=2, padx=(8, 0), pady=3
        )
        ttk.Label(database, text="Installation label").grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=3
        )
        ttk.Entry(database, textvariable=self.installation_ref_var).grid(
            row=3, column=1, columnspan=2, sticky="ew", pady=3
        )

        feature_toggles = ttk.Frame(database)
        feature_toggles.grid(row=4, column=0, columnspan=3, sticky="w", pady=(7, 2))
        ttk.Checkbutton(
            feature_toggles, text="Enable HASK", variable=self.hask_enabled_var
        ).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(
            feature_toggles,
            text="Enable HASK Preview",
            variable=self.hask_preview_enabled_var,
        ).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(
            feature_toggles,
            text="Enable candidate bridge",
            variable=self.candidate_enabled_var,
        ).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(
            feature_toggles,
            text="Enable native domain status",
            variable=self.native_status_enabled_var,
        ).pack(side="left")

        database_buttons = ttk.Frame(database)
        database_buttons.grid(row=5, column=0, columnspan=3, sticky="w", pady=(9, 0))
        ttk.Button(
            database_buttons,
            text="Initialize database identity",
            command=self.initialize_database_identity,
        ).pack(side="left")
        ttk.Button(
            database_buttons,
            text="Refresh status",
            command=self.refresh_database_status,
        ).pack(side="left", padx=(8, 0))

        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.grid(row=8, column=0, columnspan=3, sticky="e", pady=(22, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Save", style="Accent.TButton", command=self.save).pack(side="right")

        self.refresh_database_status()


    def save(self):
        token = self.token_var.get().strip()

        self.cfg["ha_url"] = self.url_var.get().strip()
        self.cfg["project_name"] = self.project_var.get().strip() or "My Smart Home"
        self.cfg["output_dir"] = self.output_var.get().strip() or "output"
        self.cfg["cache_dir"] = self.cfg.get("cache_dir", "cache")
        self.cfg["open_dashboard_after_scan"] = bool(self.auto_open_var.get())
        self._apply_database_fields(self.cfg)
        if token:
            self.cfg["token"] = token
        else:
            self.cfg.pop("token", None)
        self.cfg.pop("ha_token", None)

        saved, error = try_save_config(self.cfg, save=save_config)
        if not saved:
            messagebox.showerror("HADocs", error, parent=self)
            return
        self.cfg.pop("token", None)
        notified, error = try_config_callback(
            self.cfg,
            callback=self.on_save,
        )
        if not notified:
            messagebox.showerror("HADocs", error, parent=self)
            return
        self.destroy()

    def forget_token(self):
        try:
            from hadocs.security.credential_store import delete_home_assistant_token
            delete_home_assistant_token()
        except Exception as exc:
            messagebox.showerror("HADocs", f"Could not remove token from Windows Credential Manager:\n{exc}")
            return

        self.token_var.set("")
        self.token_status.config(text="Token removed from Windows Credential Manager")

    def _apply_database_fields(self, target):
        target["hask_database_enabled"] = bool(self.database_enabled_var.get())
        target["hask_database_path"] = self.database_path_var.get().strip()
        target["hask_database_installation_ref"] = (
            self.installation_ref_var.get().strip()
        )
        target["hask_enabled"] = bool(self.hask_enabled_var.get())
        preview_var = getattr(self, "hask_preview_enabled_var", None)
        target["hask_preview_enabled"] = (
            bool(preview_var.get())
            if preview_var is not None
            else bool(target.get("hask_preview_enabled", False))
        )
        target["hask_candidate_evidence_enabled"] = bool(
            self.candidate_enabled_var.get()
        )
        target["hask_native_integration_status_enabled"] = bool(
            self.native_status_enabled_var.get()
        )

    def _database_config(self):
        config = dict(self.cfg)
        self._apply_database_fields(config)
        config.pop("token", None)
        config.pop("ha_token", None)
        return config

    def browse_database(self):
        selected = filedialog.asksaveasfilename(
            parent=self,
            title="Select HADocs operational database",
            defaultextension=".sqlite",
            filetypes=(("SQLite database", "*.sqlite"), ("All files", "*.*")),
        )
        if selected:
            self.database_path_var.set(selected)

    def refresh_database_status(self):
        from hadocs.application.database_status import (
            read_operational_database_status,
        )

        status = read_operational_database_status(self._database_config())
        version = (
            "not available"
            if status.schema_version is None
            else str(status.schema_version)
        )
        self.database_status_var.set(
            "Persistence: {enabled}   Identity: {identity}   "
            "Protected material: {protected}   "
            "Database file: {database}\nSchema: {version}   Integrity: {integrity}   "
            "Foreign keys: {foreign_keys}".format(
                enabled="enabled" if status.enabled else "disabled",
                identity="initialized" if status.identity_initialized else "not initialized",
                protected="available" if status.protected_material_valid else "not available",
                database="present" if status.database_file_present else "not present",
                version=version,
                integrity=status.integrity_status,
                foreign_keys=status.foreign_key_status,
            )
        )

    def initialize_database_identity(self):
        if not messagebox.askyesno(
            "Initialize operational database",
            "Create protected database identity material for this HADocs installation? "
            "This does not enable database persistence.",
            parent=self,
        ):
            return

        from hadocs.application.database_status import initialize_database_identity
        from hadocs.application.operational_database import (
            DatabaseIdentityInitializationState,
        )
        from hadocs.utils.config import save_database_identity_config

        enabled_before = bool(self.database_enabled_var.get())
        try:
            result, updated = initialize_database_identity(
                self._database_config(), save=save_database_identity_config
            )
        except (RuntimeError, TypeError, ValueError):
            messagebox.showerror(
                "HADocs",
                "Database identity could not be initialized. Check the selected path, "
                "installation label, and protected credential storage.",
                parent=self,
            )
            return

        self.cfg = updated
        self.database_enabled_var.set(enabled_before)
        self.cfg["hask_database_enabled"] = enabled_before
        notified, error = try_config_callback(
            self.cfg,
            callback=self.on_save,
        )
        if not notified:
            messagebox.showerror("HADocs", error, parent=self)
            return
        self.refresh_database_status()
        message = (
            "Database identity was already initialized; no changes were made."
            if result.state is DatabaseIdentityInitializationState.ALREADY_INITIALIZED
            else (
                "Database identity initialized. The existing persistence setting was "
                "left unchanged."
                if enabled_before
                else "Database identity initialized. Database persistence remains "
                "disabled until you explicitly enable and save it."
            )
        )
        messagebox.showinfo("HADocs", message, parent=self)

from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from src.hadocs.core.device_overrides import (
    DeviceOverride,
    OWNERSHIP_VALUES,
    POLICY_TYPES,
    PURPOSE_VALUES,
    load_device_overrides_file,
    remove_device_override,
    resolve_device_overrides_file,
    upsert_device_override,
)
from src.hadocs.gui.data import safe_read_json
from src.hadocs.gui.theme import Theme

class DeviceOverrideManager(tk.Toplevel):
    """Graphical editor for config/device_overrides.json."""

    MONTHS = [
        (1, "Jan"), (2, "Feb"), (3, "Mar"), (4, "Apr"),
        (5, "May"), (6, "Jun"), (7, "Jul"), (8, "Aug"),
        (9, "Sep"), (10, "Oct"), (11, "Nov"), (12, "Dec"),
    ]

    def __init__(self, master, cfg):
        super().__init__(master)
        self.title("HADocs Device Overrides")
        self.geometry("1120x760")
        self.minsize(980, 680)
        self.transient(master)
        Theme.apply(self)

        self.cfg = dict(cfg or {})
        self.override_path = resolve_device_overrides_file(self.cfg)
        self.overrides = []
        self.devices = self._load_devices()
        self.filtered_devices = []
        self.selected_device_id = None

        self.search_var = tk.StringVar()
        self.device_id_var = tk.StringVar()
        self.device_name_var = tk.StringVar()
        self.ownership_var = tk.StringVar(value="unspecified")
        self.purpose_var = tk.StringVar(value="unspecified")
        self.policy_type_var = tk.StringVar(value="normal")
        self.expected_offline_var = tk.BooleanVar(value=False)
        self.ignore_battery_var = tk.BooleanVar(value=False)
        self.ignore_stale_var = tk.BooleanVar(value=False)
        self.reason_var = tk.StringVar()
        self.month_vars = {month: tk.BooleanVar(value=False) for month, _ in self.MONTHS}

        self._build_ui()
        self.reload()

    def _load_devices(self):
        output_dir = Path(self.cfg.get("output_dir", "output"))
        search_index = output_dir / "explorer" / "search_index.json"
        payload = safe_read_json(search_index)
        if not isinstance(payload, list):
            return []
        devices = []
        for item in payload:
            if not isinstance(item, dict) or item.get("type") != "device":
                continue
            device_id = str(item.get("id") or "").strip()
            title = str(item.get("title") or device_id).strip()
            if device_id:
                devices.append({"id": device_id, "name": title})
        return sorted(devices, key=lambda item: item["name"].casefold())

    def _build_ui(self):
        container = ttk.Frame(self, style="Panel.TFrame", padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=3)
        container.rowconfigure(2, weight=1)

        ttk.Label(container, text="Device Override Manager", style="Hero.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            container,
            text=(
                "Add, edit or remove device policies without editing JSON manually. "
                f"File: {self.override_path}"
            ),
            style="MutedPanel.TLabel",
            wraplength=1000,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 16))

        left = ttk.Frame(container, style="Card.TFrame", padding=14)
        left.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        ttk.Label(left, text="Devices", style="Card.TLabel", font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        search = ttk.Entry(left, textvariable=self.search_var)
        search.grid(row=1, column=0, sticky="ew", pady=(10, 10))
        search.bind("<KeyRelease>", lambda _event: self.refresh_device_list())

        self.device_tree = ttk.Treeview(
            left, columns=("override",), show="tree headings", selectmode="browse"
        )
        self.device_tree.heading("#0", text="Device")
        self.device_tree.heading("override", text="Override")
        self.device_tree.column("#0", width=260, stretch=True)
        self.device_tree.column("override", width=90, anchor="center", stretch=False)
        self.device_tree.grid(row=2, column=0, sticky="nsew")
        self.device_tree.bind("<<TreeviewSelect>>", self.on_device_selected)
        tree_scroll = ttk.Scrollbar(left, orient="vertical", command=self.device_tree.yview)
        tree_scroll.grid(row=2, column=1, sticky="ns")
        self.device_tree.configure(yscrollcommand=tree_scroll.set)

        ttk.Button(left, text="New manual override", command=self.clear_form).grid(
            row=3, column=0, sticky="w", pady=(12, 0)
        )

        right = ttk.Frame(container, style="Card.TFrame", padding=16)
        right.grid(row=2, column=1, sticky="nsew")
        right.columnconfigure(1, weight=1)

        ttk.Label(right, text="Override details", style="Card.TLabel", font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )

        rows = [
            ("Device ID", self.device_id_var),
            ("Device name", self.device_name_var),
        ]
        for row, (label, var) in enumerate(rows, start=1):
            ttk.Label(right, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5, padx=(0, 12))
            ttk.Entry(right, textvariable=var).grid(row=row, column=1, columnspan=2, sticky="ew", pady=5)

        choices = [
            ("Ownership", self.ownership_var, sorted(OWNERSHIP_VALUES)),
            ("Purpose", self.purpose_var, sorted(PURPOSE_VALUES)),
            ("Policy", self.policy_type_var, sorted(POLICY_TYPES)),
        ]
        for row, (label, var, values) in enumerate(choices, start=3):
            ttk.Label(right, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5, padx=(0, 12))
            combo = ttk.Combobox(right, textvariable=var, values=values, state="readonly")
            combo.grid(row=row, column=1, columnspan=2, sticky="ew", pady=5)

        flags = ttk.Frame(right, style="Card.TFrame")
        flags.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        ttk.Checkbutton(flags, text="Expected offline", variable=self.expected_offline_var).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(flags, text="Ignore battery", variable=self.ignore_battery_var).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(flags, text="Ignore stale", variable=self.ignore_stale_var).pack(side="left")

        ttk.Label(right, text="Active months", style="Card.TLabel").grid(row=7, column=0, sticky="nw", pady=(10, 4), padx=(0, 12))
        months = ttk.Frame(right, style="Card.TFrame")
        months.grid(row=7, column=1, columnspan=2, sticky="w", pady=(6, 4))
        for index, (month, label) in enumerate(self.MONTHS):
            ttk.Checkbutton(months, text=label, variable=self.month_vars[month]).grid(
                row=index // 6, column=index % 6, sticky="w", padx=(0, 8), pady=2
            )

        ttk.Label(right, text="Reason", style="Card.TLabel").grid(row=8, column=0, sticky="w", pady=(10, 5), padx=(0, 12))
        ttk.Entry(right, textvariable=self.reason_var).grid(row=8, column=1, columnspan=2, sticky="ew", pady=(10, 5))

        self.status_label = ttk.Label(right, text="", style="MutedCard.TLabel", wraplength=620)
        self.status_label.grid(row=9, column=0, columnspan=3, sticky="w", pady=(12, 0))

        buttons = ttk.Frame(right, style="Card.TFrame")
        buttons.grid(row=10, column=0, columnspan=3, sticky="e", pady=(20, 0))
        ttk.Button(buttons, text="Remove override", command=self.remove_override).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Save override", style="Accent.TButton", command=self.save_override).pack(side="left")

    def reload(self):
        try:
            self.overrides = list(load_device_overrides_file(self.override_path))
            self.status_label.config(text=f"Loaded {len(self.overrides)} override(s).")
        except ValueError as exc:
            self.overrides = []
            messagebox.showerror("Device Overrides", str(exc), parent=self)
        self.refresh_device_list()

    def override_by_id(self):
        return {item.device_id: item for item in self.overrides if item.device_id}

    def refresh_device_list(self):
        selected = self.device_id_var.get().strip()
        query = self.search_var.get().strip().casefold()
        known = {item["id"]: item for item in self.devices}
        for override in self.overrides:
            if override.device_id and override.device_id not in known:
                known[override.device_id] = {
                    "id": override.device_id,
                    "name": override.device_name or override.device_id,
                }
        self.filtered_devices = [
            item for item in known.values()
            if not query or query in item["name"].casefold() or query in item["id"].casefold()
        ]
        self.filtered_devices.sort(key=lambda item: item["name"].casefold())
        overrides = self.override_by_id()
        self.device_tree.delete(*self.device_tree.get_children())
        for item in self.filtered_devices:
            self.device_tree.insert(
                "", "end", iid=item["id"], text=item["name"],
                values=("Yes" if item["id"] in overrides else "—",)
            )
        if selected and self.device_tree.exists(selected):
            self.device_tree.selection_set(selected)
            self.device_tree.see(selected)

    def on_device_selected(self, _event=None):
        selection = self.device_tree.selection()
        if not selection:
            return
        device_id = selection[0]
        item = next((item for item in self.filtered_devices if item["id"] == device_id), None)
        override = self.override_by_id().get(device_id)
        self.selected_device_id = device_id
        self.device_id_var.set(device_id)
        self.device_name_var.set((override.device_name if override else None) or (item["name"] if item else ""))
        if override:
            self.ownership_var.set(override.ownership)
            self.purpose_var.set(override.purpose)
            self.policy_type_var.set(override.policy_type)
            self.expected_offline_var.set(override.expected_offline)
            self.ignore_battery_var.set(override.ignore_battery)
            self.ignore_stale_var.set(override.ignore_stale)
            self.reason_var.set(override.reason)
            for month, var in self.month_vars.items():
                var.set(month in override.active_months)
            self.status_label.config(text="Existing override loaded. Edit and save, or remove it.")
        else:
            self._reset_policy_fields()
            self.status_label.config(text="No override exists for this device.")

    def _reset_policy_fields(self):
        self.ownership_var.set("unspecified")
        self.purpose_var.set("unspecified")
        self.policy_type_var.set("normal")
        self.expected_offline_var.set(False)
        self.ignore_battery_var.set(False)
        self.ignore_stale_var.set(False)
        self.reason_var.set("")
        for var in self.month_vars.values():
            var.set(False)

    def clear_form(self):
        self.selected_device_id = None
        self.device_tree.selection_remove(self.device_tree.selection())
        self.device_id_var.set("")
        self.device_name_var.set("")
        self._reset_policy_fields()
        self.status_label.config(text="Enter a device ID, or select a device from the list.")

    def save_override(self):
        device_id = self.device_id_var.get().strip()
        device_name = self.device_name_var.get().strip()
        if not device_id:
            messagebox.showwarning("Device Overrides", "A device ID is required.", parent=self)
            return
        active_months = tuple(month for month, var in self.month_vars.items() if var.get())
        if self.policy_type_var.get() == "seasonal" and not active_months:
            if not messagebox.askyesno(
                "Seasonal override",
                "No active months are selected. Save the seasonal override anyway?",
                parent=self,
            ):
                return
        override = DeviceOverride(
            device_id=device_id,
            device_name=device_name or None,
            ownership=self.ownership_var.get(),
            purpose=self.purpose_var.get(),
            policy_type=self.policy_type_var.get(),
            expected_offline=bool(self.expected_offline_var.get()),
            ignore_battery=bool(self.ignore_battery_var.get()),
            ignore_stale=bool(self.ignore_stale_var.get()),
            active_months=active_months,
            reason=self.reason_var.get().strip(),
        )
        try:
            self.overrides = list(upsert_device_override(self.override_path, override))
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Device Overrides", f"Could not save override:\n{exc}", parent=self)
            return
        self.selected_device_id = device_id
        self.status_label.config(
            text="Override saved safely. Run a new scan to recalculate incidents and Health Score."
        )
        self.refresh_device_list()

    def remove_override(self):
        device_id = self.device_id_var.get().strip()
        if not device_id or device_id not in self.override_by_id():
            messagebox.showinfo("Device Overrides", "This device has no override to remove.", parent=self)
            return
        if not messagebox.askyesno(
            "Remove override", f"Remove the override for {self.device_name_var.get() or device_id}?", parent=self
        ):
            return
        try:
            self.overrides = list(remove_device_override(self.override_path, device_id))
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Device Overrides", f"Could not remove override:\n{exc}", parent=self)
            return
        self._reset_policy_fields()
        self.status_label.config(text="Override removed. Run a new scan to recalculate the analysis.")
        self.refresh_device_list()



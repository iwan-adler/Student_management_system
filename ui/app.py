"""The complete single-window Tkinter interface for the SMS."""

import csv
import sqlite3
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, simpledialog, ttk

from auth.login import authenticate, change_password
from services.data_service import DataService
from utils.calculations import calculate_gpa
from utils.validators import required, valid_date, valid_email, valid_phone


class LoginWindow(ttk.Frame):
    """First screen; only a verified administrator can open the application."""
    def __init__(self, master, on_login):
        super().__init__(master, padding=35)
        self.on_login = on_login
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text="Student Management System", style="Title.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 28))
        self.username = self._field("Username", 1)
        self.password = self._field("Password", 2, show="•")
        ttk.Button(self, text="Login", command=self.login).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 6))
        ttk.Button(self, text="Exit", command=master.destroy).grid(row=4, column=0, columnspan=2, sticky="ew")
        self.username.focus_set()

    def _field(self, label, row, show=None):
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=7)
        entry = ttk.Entry(self, show=show, width=28)
        entry.grid(row=row, column=1, sticky="ew", pady=7)
        return entry

    def login(self):
        username, password = self.username.get().strip(), self.password.get()
        if not username or not password:
            messagebox.showerror("Login", "Enter both username and password.")
            return
        user = authenticate(username, password)
        if not user:
            messagebox.showerror("Login", "Invalid username or password.")
            return
        if user["must_change_password"]:
            new_password = simpledialog.askstring("Change default password", "Enter a new password (minimum 6 characters):", show="•", parent=self)
            if not new_password or len(new_password) < 6:
                messagebox.showwarning("Password required", "Please log in again and choose a password with at least 6 characters.")
                return
            change_password(user["id"], new_password)
        self.on_login()


class MainApplication(ttk.Frame):
    """Dashboard-style app shell and module views."""
    def __init__(self, master):
        super().__init__(master)
        self.service = DataService()
        self.current_view = None
        self.pack(fill="both", expand=True)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(self, padding=12, style="Side.TFrame")
        sidebar.grid(row=0, column=0, sticky="nsew")
        ttk.Label(sidebar, text="SMS", style="SideTitle.TLabel").pack(anchor="w", pady=(5, 20))
        for text, action in (("Dashboard", self.dashboard), ("Students", self.students), ("Subjects", self.subjects), ("Academics", self.academics), ("Attendance", self.attendance), ("Fees", self.fees), ("Reports", self.reports), ("Settings", self.settings)):
            ttk.Button(sidebar, text=text, command=action, style="Side.TButton").pack(fill="x", pady=3)
        ttk.Separator(sidebar).pack(fill="x", pady=16)
        ttk.Button(sidebar, text="Logout", command=self.logout, style="Side.TButton").pack(fill="x")
        self.content = ttk.Frame(self, padding=20)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1)
        self.dashboard()

    def logout(self):
        if messagebox.askyesno("Logout", "Log out of the application?"):
            self.destroy()
            LoginWindow(self.master, self.show_app).pack(expand=True)

    def show_app(self):
        for child in self.master.winfo_children(): child.destroy()
        MainApplication(self.master)

    def clear(self, title):
        for child in self.content.winfo_children(): child.destroy()
        ttk.Label(self.content, text=title, style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 15))

    def tree(self, parent, columns, headings):
        frame = ttk.Frame(parent)
        frame.grid(row=1, column=0, sticky="nsew")
        parent.rowconfigure(1, weight=1)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for key, title in zip(columns, headings):
            tree.heading(key, text=title, command=lambda c=key: self.sort_tree(tree, c, False))
            tree.column(key, width=120, minwidth=70)
        ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew"); ybar.grid(row=0, column=1, sticky="ns"); xbar.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        return tree

    @staticmethod
    def sort_tree(tree, column, reverse):
        values = [(tree.set(item, column), item) for item in tree.get_children("")]
        try: values.sort(key=lambda pair: float(pair[0]), reverse=reverse)
        except ValueError: values.sort(reverse=reverse)
        for index, (_, item) in enumerate(values): tree.move(item, "", index)
        tree.heading(column, command=lambda: MainApplication.sort_tree(tree, column, not reverse))

    def dashboard(self):
        self.clear("Dashboard")
        cards = ttk.Frame(self.content); cards.grid(row=1, column=0, sticky="new")
        stats = self.service.dashboard()
        for i, (label, value) in enumerate(stats.items()):
            card = ttk.LabelFrame(cards, text=label, padding=15)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=6, pady=6)
            display = f"₹{value:,.2f}" if label == "Pending Fees" else f"{value:.2f}%" if label == "Average Attendance" else f"{value:.2f}" if label == "Average GPA" else str(value)
            ttk.Label(card, text=display, style="Card.TLabel").pack()
        for i in range(3): cards.columnconfigure(i, weight=1)
        ttk.Label(self.content, text="Grade distribution", style="Heading.TLabel").grid(row=2, column=0, sticky="w", pady=(24, 6))
        distribution = ttk.Frame(self.content)
        distribution.grid(row=3, column=0, sticky="nsew")
        self.content.rowconfigure(3, weight=1)
        tree = self.tree(distribution, ("grade", "students"), ("Grade", "Records"))
        for row in self.service.rows("SELECT grade, COUNT(*) AS count FROM marks GROUP BY grade ORDER BY grade"):
            tree.insert("", "end", values=(row["grade"], row["count"]))

    def students(self):
        self.clear("Students")
        controls = ttk.Frame(self.content); controls.grid(row=1, column=0, sticky="ew", pady=(0, 10)); controls.columnconfigure(0, weight=1)
        search = ttk.Entry(controls); search.grid(row=0, column=0, sticky="ew", padx=(0, 8)); search.insert(0, "Search ID, roll number, name, department, course")
        department = ttk.Combobox(controls, values=["All"] + [r["department"] for r in self.service.rows("SELECT DISTINCT department FROM students ORDER BY department")], state="readonly", width=16); department.set("All"); department.grid(row=0, column=1, padx=3)
        year = ttk.Combobox(controls, values=["All", "1", "2", "3", "4"], state="readonly", width=7); year.set("All"); year.grid(row=0, column=2, padx=3)
        sem = ttk.Combobox(controls, values=["All"] + [str(i) for i in range(1, 9)], state="readonly", width=7); sem.set("All"); sem.grid(row=0, column=3, padx=3)
        gender = ttk.Combobox(controls, values=["All", "Male", "Female", "Other"], state="readonly", width=9); gender.set("All"); gender.grid(row=0, column=4, padx=3)
        holder = ttk.Frame(self.content); holder.grid(row=2, column=0, sticky="nsew"); self.content.rowconfigure(2, weight=1)
        tree = self.tree(holder, ("id", "student_id", "roll", "name", "department", "course", "year", "semester", "phone", "email"), ("DB ID", "Student ID", "Roll No", "Name", "Department", "Course", "Year", "Semester", "Phone", "Email")); tree.column("id", width=55)
        def refresh(*_):
            term = search.get().strip(); term = "" if term.startswith("Search ") else term
            tree.delete(*tree.get_children())
            for r in self.service.students(term, department.get(), year.get(), sem.get(), gender.get()): tree.insert("", "end", values=(r["id"], r["student_id"], r["roll_number"], r["name"], r["department"], r["course"], r["year"], r["semester"], r["phone"], r["email"]))
        for widget in (search, department, year, sem, gender): widget.bind("<KeyRelease>", refresh); widget.bind("<<ComboboxSelected>>", refresh)
        ttk.Button(controls, text="Refresh", command=refresh).grid(row=0, column=5, padx=3)
        ttk.Button(controls, text="Add / Edit", command=lambda: self.student_form(tree, refresh)).grid(row=0, column=6, padx=3)
        ttk.Button(controls, text="Delete", command=lambda: self.delete_selected(tree, self.service.delete_student, refresh, "student")).grid(row=0, column=7, padx=3)
        refresh()

    def student_form(self, tree, refresh):
        selected = tree.selection(); record = self.service.row("SELECT * FROM students WHERE id=?", (tree.item(selected[0])["values"][0],)) if selected else None
        fields = [("student_id", "Student ID"), ("roll_number", "Roll Number"), ("name", "Full Name"), ("dob", "Date of Birth (YYYY-MM-DD)"), ("gender", "Gender"), ("email", "Email"), ("phone", "Phone"), ("address", "Address"), ("department", "Department"), ("course", "Course"), ("year", "Year"), ("semester", "Semester"), ("admission_date", "Admission Date (YYYY-MM-DD)")]
        window, entries = self.form_window("Student", fields, record)
        def save():
            data = {key: entry.get().strip() for key, entry in entries.items()}
            errors = [required(data[x], label) for x, label in fields if x in ("student_id", "roll_number", "name", "department", "course", "year", "semester", "admission_date")]
            if not valid_email(data["email"]): errors.append("Enter a valid email address.")
            if not valid_phone(data["phone"]): errors.append("Enter a valid phone number.")
            if not valid_date(data["dob"]) or not valid_date(data["admission_date"]): errors.append("Dates must use YYYY-MM-DD.")
            try: data["year"], data["semester"] = int(data["year"]), int(data["semester"])
            except ValueError: errors.append("Year and semester must be whole numbers.")
            errors = [e for e in errors if e]
            if errors: return messagebox.showerror("Student", "\n".join(errors), parent=window)
            try: self.service.save_student(data, record["id"] if record else None)
            except sqlite3.IntegrityError: return messagebox.showerror("Student", "Student ID and Roll Number must be unique.", parent=window)
            window.destroy(); refresh(); messagebox.showinfo("Student", "Student saved.")
        ttk.Button(window, text="Save", command=save).grid(row=len(fields)+1, column=0, columnspan=2, sticky="ew", pady=12)

    def subjects(self):
        self.clear("Subjects")
        controls = ttk.Frame(self.content); controls.grid(row=1, column=0, sticky="ew", pady=(0, 10)); controls.columnconfigure(0, weight=1)
        search = ttk.Entry(controls); search.grid(row=0, column=0, sticky="ew", padx=(0, 8)); search.insert(0, "Search subject")
        holder = ttk.Frame(self.content); holder.grid(row=2, column=0, sticky="nsew"); self.content.rowconfigure(2, weight=1)
        tree = self.tree(holder, ("id", "code", "name", "department", "semester", "credits"), ("DB ID", "Code", "Subject", "Department", "Semester", "Credits"))
        def refresh(*_):
            term = "" if search.get().startswith("Search ") else search.get(); tree.delete(*tree.get_children())
            for r in self.service.subjects(term): tree.insert("", "end", values=(r["id"], r["subject_code"], r["subject_name"], r["department"], r["semester"], r["credits"]))
        search.bind("<KeyRelease>", refresh); ttk.Button(controls, text="Add / Edit", command=lambda: self.subject_form(tree, refresh)).grid(row=0, column=1, padx=3); ttk.Button(controls, text="Delete", command=lambda: self.delete_selected(tree, self.service.delete_subject, refresh, "subject")).grid(row=0, column=2, padx=3); refresh()

    def subject_form(self, tree, refresh):
        selected = tree.selection(); record = self.service.row("SELECT * FROM subjects WHERE id=?", (tree.item(selected[0])["values"][0],)) if selected else None
        fields = [("subject_code", "Subject Code"), ("subject_name", "Subject Name"), ("department", "Department"), ("semester", "Semester"), ("credits", "Credits")]
        window, entries = self.form_window("Subject", fields, record)
        def save():
            data = {k: e.get().strip() for k, e in entries.items()}
            errors = [required(data[k], label) for k, label in fields]
            try: data["semester"], data["credits"] = int(data["semester"]), int(data["credits"])
            except ValueError: errors.append("Semester and credits must be whole numbers.")
            if any(errors): return messagebox.showerror("Subject", "\n".join(e for e in errors if e), parent=window)
            try: self.service.save_subject(data, record["id"] if record else None)
            except sqlite3.IntegrityError: return messagebox.showerror("Subject", "Subject code must be unique.", parent=window)
            window.destroy(); refresh()
        ttk.Button(window, text="Save", command=save).grid(row=len(fields)+1, column=0, columnspan=2, sticky="ew", pady=12)

    def academics(self): self.record_module("Academics / Marks", "marks")
    def attendance(self): self.record_module("Attendance", "attendance")
    def fees(self): self.record_module("Fees", "fees")

    def record_module(self, title, module):
        self.clear(title); top = ttk.Frame(self.content); top.grid(row=1, column=0, sticky="ew", pady=(0, 10)); top.columnconfigure(0, weight=1)
        if module == "marks":
            columns, headings, rows = ("student", "subject", "internal", "external", "total", "grade", "year", "semester"), ("Student", "Subject", "Internal", "External", "Total", "Grade", "Year", "Semester"), self.service.mark_rows
        elif module == "attendance":
            columns, headings, rows = ("student", "subject", "total", "attended", "absent", "percent", "year", "semester"), ("Student", "Subject", "Total", "Attended", "Absent", "%", "Year", "Semester"), self.service.attendance_rows
        else:
            columns, headings, rows = ("student", "year", "total", "paid", "pending", "status", "date"), ("Student", "Year", "Total Fee", "Paid", "Pending", "Status", "Last Payment"), self.service.fee_rows
        holder = ttk.Frame(self.content); holder.grid(row=2, column=0, sticky="nsew"); self.content.rowconfigure(2, weight=1); tree = self.tree(holder, columns, headings)
        def refresh():
            tree.delete(*tree.get_children())
            for r in rows():
                if module == "marks": values=(f"{r['student_id']} — {r['name']}", r['subject_code'], r['internal_marks'], r['external_marks'], r['total_marks'], r['grade'], r['academic_year'], r['semester'])
                elif module == "attendance": values=(f"{r['student_id']} — {r['name']}", r['subject_code'], r['total_classes'], r['attended_classes'], r['total_classes']-r['attended_classes'], r['attendance_percentage'], r['academic_year'], r['semester'])
                else: values=(f"{r['student_id']} — {r['name']}", r['academic_year'], r['total_fee'], r['paid_amount'], r['pending_amount'], r['payment_status'], r['last_payment_date'] or "")
                tree.insert("", "end", values=values)
        ttk.Button(top, text="Add / Update Record", command=lambda: self.record_form(module, refresh)).grid(row=0, column=1); ttk.Button(top, text="Refresh", command=refresh).grid(row=0, column=2, padx=4); refresh()

    def record_form(self, module, refresh):
        window = tk.Toplevel(self); window.title("Add / Update Record"); window.transient(self); window.grab_set(); window.columnconfigure(1, weight=1); window.configure(padx=20, pady=20)
        students, subjects = self.service.student_choices(), self.service.subject_choices(); lookup_s={r['label']:r['id'] for r in students}; lookup_sub={r['label']:r['id'] for r in subjects}
        fields = [("student", "Student", list(lookup_s)), ("subject", "Subject", list(lookup_sub))]
        if module == "marks": fields += [("first", "Internal (0–40)", None), ("second", "External (0–60)", None), ("year", "Academic Year", None), ("semester", "Semester", None)]
        elif module == "attendance": fields += [("first", "Total Classes", None), ("second", "Classes Attended", None), ("year", "Academic Year", None), ("semester", "Semester", None)]
        else: fields = [("student", "Student", list(lookup_s)), ("year", "Academic Year", None), ("first", "Total Fee", None), ("second", "Paid Amount", None), ("date", "Last Payment (YYYY-MM-DD)", None)]
        entries={}
        for i,(key,label,options) in enumerate(fields):
            ttk.Label(window,text=label).grid(row=i,column=0,sticky="w",padx=(0,10),pady=5)
            widget=ttk.Combobox(window, values=options, state="readonly") if options else ttk.Entry(window)
            widget.grid(row=i,column=1,sticky="ew",pady=5); entries[key]=widget
        entries["year"].insert(0,"2026-27") if "year" in entries else None
        if "semester" in entries: entries["semester"].insert(0,"1")
        def save():
            try:
                student=lookup_s[entries['student'].get()]; year=entries['year'].get().strip();
                if not year: raise ValueError("Academic year is required.")
                if module == "marks":
                    internal, external=float(entries['first'].get()),float(entries['second'].get()); semester=int(entries['semester'].get());
                    if not 0<=internal<=40 or not 0<=external<=60: raise ValueError("Internal must be 0–40 and external must be 0–60.")
                    self.service.save_mark(student, lookup_sub[entries['subject'].get()], internal, external, year, semester)
                elif module == "attendance":
                    total, attended=int(entries['first'].get()),int(entries['second'].get()); semester=int(entries['semester'].get());
                    if total<0 or attended<0 or attended>total: raise ValueError("Attended classes must be between 0 and total classes.")
                    self.service.save_attendance(student, lookup_sub[entries['subject'].get()], total, attended, year, semester)
                else:
                    total, paid=float(entries['first'].get()),float(entries['second'].get()); payment_date=entries['date'].get().strip()
                    if total<0 or paid<0 or paid>total: raise ValueError("Paid amount must be between 0 and total fee.")
                    if payment_date and not valid_date(payment_date): raise ValueError("Payment date must use YYYY-MM-DD.")
                    self.service.save_fee(student, year, total, paid, payment_date)
            except (ValueError, KeyError) as error: return messagebox.showerror("Record", str(error), parent=window)
            window.destroy(); refresh(); messagebox.showinfo("Record", "Record saved.")
        ttk.Button(window,text="Save",command=save).grid(row=len(fields)+1,column=0,columnspan=2,sticky="ew",pady=12)

    def reports(self):
        self.clear("Reports"); top=ttk.Frame(self.content); top.grid(row=1,column=0,sticky="ew",pady=(0,10)); top.columnconfigure(0,weight=1)
        choices=self.service.student_choices(); lookup={r['label']:r['id'] for r in choices}; selector=ttk.Combobox(top,values=list(lookup),state="readonly"); selector.grid(row=0,column=0,sticky="ew",padx=(0,8)); selector.set("Select a student for profile report")
        output=tk.Text(self.content,wrap="word",font=("Consolas",10)); output.grid(row=2,column=0,sticky="nsew"); self.content.rowconfigure(2,weight=1)
        def profile():
            if selector.get() not in lookup: return messagebox.showwarning("Reports","Choose a student.")
            student, marks, attendance, fees=self.service.profile(lookup[selector.get()]); output.delete("1.0","end")
            output.insert("end",f"STUDENT PROFILE REPORT\n{'='*60}\n{student['name']} ({student['student_id']})\nRoll No: {student['roll_number']}\nDepartment: {student['department']} | Course: {student['course']}\n\nACADEMICS\n")
            for r in marks: output.insert("end",f"{r['subject_code']}: {r['total_marks']}/100  {r['grade']}  ({r['credits']} credits)\n")
            output.insert("end",f"GPA: {calculate_gpa(marks):.2f}\n\nATTENDANCE\n")
            for r in attendance: output.insert("end",f"{r['subject_code']}: {r['attended_classes']}/{r['total_classes']} ({r['attendance_percentage']}%)\n")
            output.insert("end","\nFEES\n")
            for r in fees: output.insert("end",f"{r['academic_year']}: Total ₹{r['total_fee']:.2f}, Paid ₹{r['paid_amount']:.2f}, Pending ₹{r['pending_amount']:.2f} — {r['payment_status']}\n")
        def performance():
            output.delete("1.0","end"); output.insert("end","PERFORMANCE REPORT\n"+"="*60+"\n")
            for r in self.service.rows("SELECT st.student_id, st.name, ROUND(AVG(m.total_marks),2) average_mark FROM marks m JOIN students st ON st.id=m.student_id GROUP BY st.id ORDER BY average_mark DESC LIMIT 10"): output.insert("end",f"{r['student_id']} — {r['name']}: {r['average_mark']}%\n")
            output.insert("end","\nGRADE DISTRIBUTION\n")
            for r in self.service.rows("SELECT grade, COUNT(*) count FROM marks GROUP BY grade ORDER BY grade"): output.insert("end",f"{r['grade']}: {r['count']}\n")
        def export():
            path=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text files","*.txt")]);
            if path: open(path,"w",encoding="utf-8").write(output.get("1.0","end")); messagebox.showinfo("Reports","Report exported.")
        ttk.Button(top,text="Student Profile",command=profile).grid(row=0,column=1,padx=3); ttk.Button(top,text="Performance",command=performance).grid(row=0,column=2,padx=3); ttk.Button(top,text="Export Text",command=export).grid(row=0,column=3,padx=3)

    def settings(self):
        self.clear("Settings"); panel=ttk.Frame(self.content); panel.grid(row=1,column=0,sticky="nw"); threshold=self.service.row("SELECT value FROM settings WHERE key='attendance_threshold'")["value"]
        ttk.Label(panel,text="Low attendance threshold (%)").grid(row=0,column=0,sticky="w",padx=(0,10)); entry=ttk.Entry(panel); entry.insert(0,threshold); entry.grid(row=0,column=1)
        def save_threshold():
            try:
                value=float(entry.get());
                if not 0<=value<=100: raise ValueError
            except ValueError: return messagebox.showerror("Settings","Enter a value between 0 and 100.")
            self.service.execute("UPDATE settings SET value=? WHERE key='attendance_threshold'",(str(value),)); messagebox.showinfo("Settings","Threshold saved.")
        ttk.Button(panel,text="Save",command=save_threshold).grid(row=0,column=2,padx=8)
        def samples():
            if self.service.populate_sample_data(): messagebox.showinfo("Sample data","10 students and related demo records added.")
            else: messagebox.showwarning("Sample data","Sample data is only added to an empty database.")
        ttk.Button(panel,text="Initialize sample data",command=samples).grid(row=1,column=0,columnspan=3,sticky="ew",pady=18)
        def clear_data():
            if messagebox.askyesno("Clear data", "Remove all students, subjects, marks, attendance, and fees? The administrator account will remain."):
                self.service.clear_demo_data(); messagebox.showinfo("Settings", "Operational data cleared.")
        ttk.Button(panel,text="Clear operational data",command=clear_data).grid(row=2,column=0,columnspan=3,sticky="ew")

    def form_window(self, title, fields, record):
        window=tk.Toplevel(self); window.title(title); window.transient(self); window.grab_set(); window.configure(padx=20,pady=20); window.columnconfigure(1,weight=1); entries={}
        for i,(key,label) in enumerate(fields):
            ttk.Label(window,text=label).grid(row=i,column=0,sticky="w",padx=(0,10),pady=4); entry=ttk.Entry(window,width=35); entry.grid(row=i,column=1,sticky="ew",pady=4); entry.insert(0,str(record[key] or "") if record else ""); entries[key]=entry
        return window,entries

    @staticmethod
    def delete_selected(tree, callback, refresh, label):
        selected=tree.selection()
        if not selected: return messagebox.showwarning("Delete",f"Select a {label} first.")
        if messagebox.askyesno("Confirm delete",f"Are you sure you want to delete this {label}? This cannot be undone."):
            try: callback(tree.item(selected[0])["values"][0]); refresh()
            except sqlite3.IntegrityError: messagebox.showerror("Delete",f"This {label} is used by existing records and cannot be deleted.")

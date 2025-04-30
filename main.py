import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
from tkcalendar import DateEntry
import tkinter as tk
from tkinter import *
import tkinter.messagebox as mb
import tkinter.ttk as ttk

# Connecting to the Database
connector = sqlite3.connect("Expense Tracker.db")
cursor = connector.cursor()

connector.execute(
    'CREATE TABLE IF NOT EXISTS ExpenseTracker (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, Date DATETIME, Payee TEXT, Description TEXT, Amount FLOAT, ModeOfPayment TEXT)'
)
connector.commit()

# Functions
# Function to generate pie chart
def show_graph():
    graph_window = tk.Toplevel(root)
    graph_window.title('Expense Tracker Graph')
    graph_window.geometry('800x600')

    try:
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        cursor.execute('SELECT Payee, ModeOfPayment, SUM(Amount) FROM ExpenseTracker GROUP BY Payee, ModeOfPayment')
        data = cursor.fetchall()

        if not data:
            print("No data found in the database.")
            mb.showerror("Error", "No data found in the database.")
            return

        payees = list(set([item[0] for item in data]))
        modes_of_payment = list(set([item[1] for item in data]))
        amounts = [[0 for _ in range(len(modes_of_payment))] for _ in range(len(payees))]

        for item in data:
            payee_index = payees.index(item[0])
            mode_index = modes_of_payment.index(item[1])
            amounts[payee_index][mode_index] = item[2]

        ax.bar(payees, [sum(amount) for amount in amounts], label='Total')
        for i, mode in enumerate(modes_of_payment):
            ax.bar(payees, [amount[i] for amount in amounts], label=mode)

        ax.set_xlabel('Payee')
        ax.set_ylabel('Amount')
        ax.set_title('Expense Tracker Graph')
        ax.tick_params(axis='x', rotation=90)
        ax.legend()

        # Display remaining balance on the graph
        remaining_balance = budget.get()
        ax.text(0.05, 0.9, f"Remaining Budget: ${remaining_balance:.2f}", transform=ax.transAxes, fontsize=15, fontweight='bold')

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
    except sqlite3.Error as e:
        print("An error occurred while fetching data:", e)
        mb.showerror("Error", "An error occurred while fetching data.")
def list_all_expenses():
    global connector, table

    table.delete(*table.get_children())

    all_data = connector.execute('SELECT * FROM ExpenseTracker')
    data = all_data.fetchall()

    for values in data:
        table.insert('', END, values=values)

def set_budget():
    global budget_label, budget_entry, budget

    new_budget = float(budget_entry.get())
    budget.set(new_budget)
    mb.showinfo("Budget Updated", f"Budget has been updated to ${new_budget}")

def add_another_expense():
    global date, desc, amnt, payee, MoP, budget
    global connector

    if not date.get() or not desc.get() or not amnt.get() or not payee.get() or not MoP.get():
        mb.showerror('Fields empty!', "Please fill all the missing fields before pressing the add button!")
    else:
        amount = amnt.get()
        if amount > budget.get():
            mb.showerror('Budget Exceeded', "Expense amount exceeds the budget!")
            return

        connector.execute(
            'INSERT INTO ExpenseTracker (Date, Payee, Description, Amount, ModeOfPayment) VALUES (?, ?, ?, ?, ?)',
            (date.get_date(), payee.get(), desc.get(), amount, MoP.get())
        )
        connector.commit()

        clear_fields()
        list_all_expenses()
        new_budget = budget.get() - amount
        budget.set(new_budget)  # Update budget after adding expense
        budget_label.config(textvariable=budget)  # Update budget label text
        mb.showinfo('Expense added', 'The expense whose details you just entered has been added to the database')

def clear_fields():
    global desc, payee, amnt, MoP, date, table

    today_date = datetime.datetime.now().date()

    desc.set('')
    payee.set('')
    amnt.set(0.0)
    MoP.set('Cash')
    date.set_date(today_date)
    table.selection_remove(*table.selection())
# Functions for Button Frame
def delete_expense():
    global connector, table

    selected_item = table.selection()
    if not selected_item:
        mb.showerror('No Expense Selected', 'Please select an expense to delete!')
        return

    confirmation = mb.askyesno('Confirm Deletion', 'Are you sure you want to delete the selected expense?')
    if confirmation:
        item_id = table.item(selected_item)['values'][0]
        connector.execute('DELETE FROM ExpenseTracker WHERE ID = ?', (item_id,))
        connector.commit()
        list_all_expenses()
        mb.showinfo('Expense Deleted', 'The selected expense has been successfully deleted!')

def clear_data_entry_fields():
    clear_fields()
    mb.showinfo('Fields Cleared', 'All fields in the data entry frame have been cleared successfully!')

def delete_all_expenses():
    global connector

    confirmation = mb.askyesno('Confirm Deletion', 'Are you sure you want to delete all expenses?')
    if confirmation:
        connector.execute('DELETE FROM ExpenseTracker')
        connector.commit()
        list_all_expenses()
        mb.showinfo('All Expenses Deleted', 'All expenses have been successfully deleted!')

def view_selected_expense_details():
    selected_item = table.selection()
    if not selected_item:
        mb.showerror('No Expense Selected', 'Please select an expense to view its details!')
        return

    item_details = table.item(selected_item)['values']
    mb.showinfo('Expense Details', f'''
        Date: {item_details[1]}
        Payee: {item_details[2]}
        Description: {item_details[3]}
        Amount: ${item_details[4]}
        Mode of Payment: {item_details[5]}
    ''')

def edit_selected_expense():
    selected_item = table.selection()
    if not selected_item:
        mb.showerror('No Expense Selected', 'Please select an expense to edit!')
        return

    item_details = table.item(selected_item)['values']

    # Convert date string to datetime object
    expense_date = datetime.datetime.strptime(item_details[1], '%Y-%m-%d')

    # Create a Toplevel window for editing expense
    edit_window = tk.Toplevel(root)
    edit_window.title('Edit Expense')
    edit_window.geometry('400x300')

    # Create a Canvas widget
    canvas = Canvas(edit_window)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    # Add a Scrollbar to the Canvas
    scrollbar = Scrollbar(edit_window, orient=VERTICAL, command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)

    # Configure the Canvas to use the Scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Create a Frame inside the Canvas to hold the content
    frame = Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # Labels for displaying current details
    Label(frame, text='Current Details', font=('Montserrat', 14, 'bold')).pack(pady=10)

    Label(frame, text=f'Date: {expense_date.strftime("%m/%d/%y")}', font=('Montserrat', 12)).pack()
    Label(frame, text=f'Payee: {item_details[2]}', font=('Montserrat', 12)).pack()
    Label(frame, text=f'Description: {item_details[3]}', font=('Montserrat', 12)).pack()
    Label(frame, text=f'Amount: ${item_details[4]}', font=('Montserrat', 12)).pack()
    Label(frame, text=f'Mode of Payment: {item_details[5]}', font=('Montserrat', 12)).pack()

    # Entry fields for editing details
    Label(frame, text='Edit Details', font=('Montserrat', 14, 'bold')).pack(pady=10)

    new_date = DateEntry(frame, date=expense_date, font=("Montserrat", 12))
    new_date.pack(pady=5)

    new_payee = Entry(frame, font=("Montserrat", 12))
    new_payee.insert(END, item_details[2])
    new_payee.pack(pady=5)

    new_desc = Entry(frame, font=("Montserrat", 12))
    new_desc.insert(END, item_details[3])
    new_desc.pack(pady=5)

    new_amount = Entry(frame, font=("Montserrat", 12))
    new_amount.insert(END, item_details[4])
    new_amount.pack(pady=5)

    new_MoP = StringVar(value=item_details[5])
    new_dd1 = OptionMenu(frame, new_MoP, *['Cash', 'Cheque', 'Credit Card', 'Debit Card', 'Paytm', 'Google Pay', 'Razorpay'])
    new_dd1.pack(pady=5)
    new_dd1.configure(width=10, font=("Montserrat", 12))

    # Update button
    def update_expense():
        new_values = (new_date.get_date(), new_payee.get(), new_desc.get(), float(new_amount.get()), new_MoP.get(), item_details[0])
        connector.execute('UPDATE ExpenseTracker SET Date=?, Payee=?, Description=?, Amount=?, ModeOfPayment=? WHERE ID=?', new_values)
        connector.commit()
        list_all_expenses()
        edit_window.destroy()
        mb.showinfo('Expense Updated', 'The expense has been successfully updated!')

    Button(frame, text='Update Expense', command=update_expense, font=("Montserrat", 12, 'bold')).pack(pady=10)

    # Configure the Canvas scrolling region
    frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

# Initializing the GUI window
root = tk.Tk()
root.title('Expense Tracker')
root.geometry('1400x550')
root.resizable(False, False)
graph_frame=Frame(root)
graph_frame.place(relx=0.7, rely=0.45, relwidth=0.3, relheight=0.5)

Label(root, text='EXPENSE TRACKER', fg="#3c49c2", font=('Montserrat', 15, 'bold'), bg='Black').pack(side=TOP, fill=X)

# StringVar and DoubleVar variables
desc = StringVar()
amnt = DoubleVar()
payee = StringVar()
MoP = StringVar(value='Cash')
budget = DoubleVar(value=0.0)

# Frames
data_entry_frame = Frame(root, bg='#1c1c1c')
data_entry_frame.place(x=0, y=30, relheight=0.95, relwidth=0.3)

buttons_frame = Frame(root, bg='#1c1c1c')
buttons_frame.place(relx=0.3, rely=0.0455, relwidth=0.7, relheight=0.21)

tree_frame = Frame(root)
tree_frame.place(relx=0.3, rely=0.26, relwidth=0.7, relheight=0.74)

# Data Entry Frame
Label(data_entry_frame, text='Date (M/DD/YY) :', font=('Montserrat', 13, 'bold'), fg="white", bg='#1c1c1c').place(x=10, y=20)
date = DateEntry(data_entry_frame, date=datetime.datetime.now().date(), font=("Montserrat", 13))
date.place(x=160, y=20)

Label(data_entry_frame, text='Payee\t             :', font=('Montserrat', 13, 'bold'), fg="white", bg='#1c1c1c').place(x=10, y=155)
Entry(data_entry_frame, font=("Montserrat", 13), width=31, text=payee).place(x=10, y=180)

Label(data_entry_frame, text='Description           :', font=('Montserrat', 13, 'bold'), fg="white", bg='#1c1c1c').place(x=10, y=55)
Entry(data_entry_frame, font=("Montserrat", 13), width=31, text=desc).place(x=10, y=80)

Label(data_entry_frame, text='Amount\t             :', font=('Montserrat', 13, 'bold'), fg="white", bg='#1c1c1c').place(x=10, y=120)
Entry(data_entry_frame, font=("Montserrat", 13), width=14, text=amnt).place(x=170, y=120)

Label(data_entry_frame, text='Mode of Payment:', font=('Montserrat', 13, 'bold'), fg="white", bg='#1c1c1c').place(x=10, y=230)
dd1 = OptionMenu(data_entry_frame, MoP, *['Cash', 'Cheque', 'Credit Card', 'Debit Card', 'Paytm', 'Google Pay', 'Razorpay'])
dd1.place(x=170, y=220)
dd1.configure(width=10, font=("Montserrat", 13))

Label(data_entry_frame, text='Budget:', font=('Montserrat', 13, 'bold'), fg="white", bg='#1c1c1c').place(x=10, y=280)
budget_entry = Entry(data_entry_frame, font=("Montserrat", 13), width=14)
budget_entry.place(x=100, y=280)
Button(data_entry_frame, text='Set Budget', command=set_budget, font=("Montserrat", 13, 'bold'), width=10, fg="white", bg='#2d2d2d').place(x=10, y=330)
budget_label = Label(data_entry_frame, textvariable=budget, font=('Montserrat', 15, 'bold'),width= 15, fg="#3c49c2", bg='white')
budget_label.place(x=160, y=330)

Button(data_entry_frame, text='Add expense', command=add_another_expense, font=("Montserrat", 13, 'bold'), width=28, fg="white", bg='#2d2d2d').place(x=10, y=390)
#Button(data_entry_frame, text='Convert to words before adding', font=("Montserrat", 13, 'bold'), width=28, fg="white", bg='#2d2d2d').place(x=10,y=440)

# Buttons' Frame

Button(buttons_frame, text='Delete Expense', font=("Montserrat", 13, 'bold'), width=28, bg='#2d2d2d', fg="white", command=delete_expense).place(x=30, y=5)
Button(buttons_frame, text='Clear Fields in DataEntry Frame', font=("Montserrat", 13, 'bold'), width=28, bg='#2d2d2d', fg="white", command=clear_data_entry_fields).place(x=335, y=5)
Button(buttons_frame, text='Delete All Expenses', font=("Montserrat", 13, 'bold'), width=28, bg='#2d2d2d', fg="white", command=delete_all_expenses).place(x=640, y=5)
Button(buttons_frame, text='View Selected Expense\'s Details', font=("Montserrat", 13, 'bold'), width=28, bg='#2d2d2d', fg="white", command=view_selected_expense_details).place(x=30, y=65)
Button(buttons_frame, text='Edit Selected Expense', font=("Montserrat", 13, 'bold'), width=28, bg='#2d2d2d', fg="white", command=edit_selected_expense).place(x=335, y=65)
Button(buttons_frame, text='Show Graph', font=("Montserrat", 13, 'bold'), width=28, bg='#2d2d2d', fg="white", command=show_graph).place(x=640, y=65)

# Treeview Frame
table = ttk.Treeview(tree_frame, selectmode=BROWSE, columns=('ID', 'Date', 'Payee', 'Description', 'Amount', 'Mode of Payment'))

X_Scroller = Scrollbar(table, orient=HORIZONTAL, command=table.xview)
Y_Scroller = Scrollbar(table, orient=VERTICAL, command=table.yview)
X_Scroller.pack(side=BOTTOM, fill=X)
Y_Scroller.pack(side=RIGHT, fill=Y)

table.config(yscrollcommand=Y_Scroller.set, xscrollcommand=X_Scroller.set)

table.heading('ID', text='S No.', anchor=CENTER)
table.heading('Date', text='Date', anchor=CENTER)
table.heading('Payee', text='Payee', anchor=CENTER)
table.heading('Description', text='Description', anchor=CENTER)
table.heading('Amount', text='Amount', anchor=CENTER)
table.heading('Mode of Payment', text='Mode of Payment', anchor=CENTER)

table.column('#0', width=0, stretch=NO)
table.column('#1', width=50, stretch=NO)
table.column('#2', width=95, stretch=NO)  # Date column
table.column('#3', width=150, stretch=NO)  # Payee column
table.column('#4', width=325, stretch=NO)  # Title column
table.column('#5', width=135, stretch=NO)  # Amount column
table.column('#6', width=125, stretch=NO)  # Mode of Payment column

table.place(relx=0, y=0, relheight=1, relwidth=1)

list_all_expenses()

# Finalizing the GUI window
root.update()
root.mainloop()
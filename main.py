import tkinter as tk
from tkinter import messagebox
import pymongo
from datetime import datetime
import re

class carParkRecord:
    def __init__(self, master):
        self.car_plate_entry = None
        self.slot_var = None
        self.new_rate_entry = None
        self.parked_time = None
        self.master = master
        self.db_uri = "mongodb://localhost:27017/"
        self.db_name = "carParkingSystem"
        self.collection_name = "parkingRecord"
        self.collection_name2 = "parkingRate"
        client = pymongo.MongoClient(self.db_uri)
        db = client[self.db_name]
        self.collection = db[self.collection_name]
        self.collection2 = db[self.collection_name2]


    def create_user_dashboard(self, search_car_plate):
        if hasattr(self, 'user_dashboard_window'):
            return
        self.user_dashboard_window = tk.Toplevel(self.master)
        self.user_dashboard_window.title("User Dashboard")

        canvas = tk.Canvas(self.user_dashboard_window, bg="white", width=500, height=150)
        canvas.pack()
        slots = list(self.collection.find())

        def payment_window():
            payment_window = tk.Toplevel(self.user_dashboard_window)
            payment_window.title("Edit Car Info")
            frame = tk.Frame(payment_window)
            frame.pack()

            display_payment = tk.Label(payment_window, text=f"Total Payment (RM): {parking_fees}")
            display_payment.pack()
            card_button = tk.Button(payment_window, text="Pay by Credit/Dbit Card", command=lambda: self.payment(search_car_plate, self.user_dashboard_window))
            card_button.pack()
            ewallet_button = tk.Button(payment_window, text="Pay by E-Wallet", command=lambda: self.payment(search_car_plate, self.user_dashboard_window))
            ewallet_button.pack()
            cancel_button = tk.Button(payment_window, text="Cancel", command=payment_window.destroy)
            cancel_button.pack()


        # Display the slots
        slot_width = 80
        slot_height = 50
        for i, slot in enumerate(slots):
            row = i // 5
            col = i % 5
            x1 = col * slot_width
            y1 = row * slot_height
            x2 = x1 + slot_width
            y2 = y1 + slot_height
            slot_color = "red" if slot["carPlate"] == search_car_plate else "white"
            canvas.create_rectangle(x1, y1, x2, y2, fill=slot_color)
            if slot["carPlate"] == search_car_plate:
                canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=f"Slot {slot['slot']}\nYour Car")
                self.parked_time = slot ["parkTime"]
            else:
                canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=f"Slot {slot['slot']}")

        display_car_plate = tk.Label(self.user_dashboard_window, text=f"Car Plate Number: {search_car_plate}")
        display_car_plate.pack()

        #Calculate total parked hour
        total_parked_hour = self.calculate_total_parked_hour(self.parked_time)

        #Calculate parking fees
        parking_fees = self.calculate_parking_fees(total_parked_hour)

        #Display total parked hour and parking fees
        total_parked_hour_label = tk.Label(self.user_dashboard_window, text=f"Total Parked Hour: {total_parked_hour}")
        total_parked_hour_label.pack()
        parking_fees_label = tk.Label(self.user_dashboard_window, text=f"Parking Fees: {parking_fees}")
        parking_fees_label.pack()
        payment_button = tk.Button(self.user_dashboard_window, text="Proceed to Payment", command=payment_window)
        payment_button.pack()

        exit_button = tk.Button(self.user_dashboard_window, text="Exit", command=self.user_dashboard_window.destroy)
        exit_button.pack()

    def create_admin_dashboard(self):
        if hasattr(self, 'admin_dashboard_window'):
            return
        self.admin_dashboard_window = tk.Toplevel(self.master)
        self.admin_dashboard_window.title("Admin Dashboard")

        # Function to add a car
        def add_car_to_slot(add_car_window):
            slot_number = self.slot_var.get()
            car_plate = self.car_plate_entry.get().upper().replace(" ", "")

            if not re.match("^[A-Za-z0-9]+$", car_plate):
                messagebox.showwarning("Warning", "Car plate can only contain alphabets and numbers.")
                return

            existing_car = self.collection.find_one({"carPlate": car_plate})
            if existing_car:
                messagebox.showwarning("Warning", "This car plate is already parked.")
                return

            self.car_plate_entry.delete(0, tk.END)  # Clear the current text
            self.car_plate_entry.insert(0, car_plate)  # Insert the modified plate number
            if not slot_number:
                messagebox.showwarning("Warning", "Please select a slot number.")
                return
            if not car_plate:
                messagebox.showwarning("Warning", "Please enter a car plate number.")
                return
            self.add_car(slot_number, car_plate)
            refresh_dashboard()
            add_car_window.destroy()

        # Function to edit car information
        def edit_car_info(edit_car_window):
            slot_number = self.slot_var.get()
            car_plate = self.car_plate_entry.get().upper().replace(" ", "")

            if not re.match("^[A-Za-z0-9]+$", car_plate):
                messagebox.showwarning("Warning", "Car plate can only contain alphabets and numbers.")
                return

            existing_car = self.collection.find_one({"carPlate": car_plate})
            if existing_car:
                messagebox.showwarning("Warning", "This car plate is already parked.")
                return

            self.car_plate_entry.delete(0, tk.END)  # Clear the current text
            self.car_plate_entry.insert(0, car_plate)  # Insert the modified plate number
            if not slot_number:
                messagebox.showwarning("Warning", "Please select a slot number.")
                return
            if not car_plate:
                messagebox.showwarning("Warning", "Please enter a car plate number.")
                return
            self.edit_car(slot_number, car_plate)
            refresh_dashboard()
            edit_car_window.destroy()

        def remove_car(edit_car_window):
            slot_number = self.slot_var.get()
            self.remove_car(slot_number)
            refresh_dashboard()
            edit_car_window.destroy()

        def edit_parking_rate(edit_parking_rate_window):
            parking_rate = self.new_rate_entry.get()
            try:
                parking_rate = float(parking_rate)  # Convert the input to a float
                if parking_rate <= 0:
                    messagebox.showerror("Error", "Parking rate must be greater than 0.")
                else:
                    parking_rate = '{:.2f}'.format(parking_rate)  # Format to two decimal places
                    self.parking_rate(parking_rate)
                    edit_parking_rate_window.destroy()  # Close the window after successful update
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numeric value for the rate.")


        def open_add_car_window():
            add_car_window = tk.Toplevel(self.admin_dashboard_window)
            add_car_window.title("Add Car to Slot")
            frame = tk.Frame(add_car_window)
            frame.pack()
            slots = list(self.collection.find())

            # Dropdown box to select available slots
            self.slot_var = tk.StringVar()
            available_slots = [slot["slot"] for slot in slots if slot["status"] == "0"]
            if len(available_slots) == 0:
                messagebox.showerror("No Available Slot", "No Available Slot Found")
                add_car_window.destroy()
            else:
                self.slot_var.set(available_slots[0] if available_slots else "")
                slot_label = tk.Label(frame, text="Select Slot:")
                slot_label.pack()
                slot_dropdown = tk.OptionMenu(frame, self.slot_var, *available_slots)
                slot_dropdown.pack()

                # Entry box for car plate number
                car_plate_label = tk.Label(frame, text="Enter Car Plate Number:")
                car_plate_label.pack()
                self.car_plate_entry = tk.Entry(frame)
                self.car_plate_entry.pack()

                # Button to add the car
                add_button = tk.Button(frame, text="Add", command=lambda: add_car_to_slot(add_car_window))
                add_button.pack()

        def open_edit_car_window():
            edit_car_window = tk.Toplevel(self.admin_dashboard_window)
            edit_car_window.title("Edit Car Info")
            frame = tk.Frame(edit_car_window)
            frame.pack()
            slots = list(self.collection.find())

            # Dropdown box to select slot for editing
            self.slot_var = tk.StringVar()
            used_slots = [slot["slot"] for slot in slots if slot["status"] == "1"]
            if len(used_slots) == 0:
                messagebox.showerror("No Car", "No Car Found")
                edit_car_window.destroy()
            else:
                self.slot_var.set(used_slots[0] if used_slots else "")
                slot_label = tk.Label(frame, text="Select Slot:")
                slot_label.pack()
                slot_dropdown = tk.OptionMenu(frame, self.slot_var, *used_slots)
                slot_dropdown.pack()

                # Entry box for car plate number
                car_plate_label = tk.Label(frame, text="Enter Car Plate Number:")
                car_plate_label.pack()
                self.car_plate_entry = tk.Entry(frame)
                self.car_plate_entry.pack()

                # Button to update car info
                update_button = tk.Button(frame, text="Update Car Info", command=lambda: edit_car_info(edit_car_window))
                update_button.pack()

                # Button to remove car
                remove_button = tk.Button(frame, text="Remove Car", command=lambda: remove_car(edit_car_window))
                remove_button.pack()

        def open_edit_parking_rate_window():
            edit_parking_rate_window = tk.Toplevel(self.admin_dashboard_window)
            edit_parking_rate_window.title("Edit Car Info")
            frame = tk.Frame(edit_parking_rate_window)
            frame.pack()
            current_rate = self.collection2.find_one()["rate"]  # Get the current parking rate

            # Label to display the current rate
            current_rate_label = tk.Label(frame, text=f"Current Rate (RM): {current_rate}")
            current_rate_label.pack()

            # Entry box for entering the new rate
            new_rate_label = tk.Label(frame, text="Enter New Rate (RM):")
            new_rate_label.pack()
            self.new_rate_entry = tk.Entry(frame)
            self.new_rate_entry.pack()

            update_button = tk.Button(frame, text="Update Parking Rate", command=lambda: edit_parking_rate(edit_parking_rate_window))
            update_button.pack()

        # Button to open the pop-up window for adding a car
        add_car_button = tk.Button(self.admin_dashboard_window, text="Add Car", command=open_add_car_window)
        add_car_button.pack()

        # Button to open the pop-up window for editing car info
        edit_car_button = tk.Button(self.admin_dashboard_window, text="Edit Car Info", command=open_edit_car_window)
        edit_car_button.pack()

        edit_parking_rate_button = tk.Button(self.admin_dashboard_window, text="Edit Parking Rate", command=open_edit_parking_rate_window)
        edit_parking_rate_button.pack()

        def refresh_dashboard():
            # Clear the current canvas display
            canvas.delete("all")

            # Retrieve the latest data from the database
            slots = list(self.collection.find())

            # Display the slots
            slot_width = 80
            slot_height = 50
            for i, slot in enumerate(slots):
                row = i // 5
                col = i % 5
                x1 = col * slot_width
                y1 = row * slot_height
                x2 = x1 + slot_width
                y2 = y1 + slot_height
                slot_color = "green" if slot["status"] == "0" else "red"
                canvas.create_rectangle(x1, y1, x2, y2, fill=slot_color)
                if slot["status"] == "0":
                    canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=f"Slot {slot['slot']}\nAvailable")
                else:
                    canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                                            text=f"Slot {slot['slot']}\n{slot['carPlate']}")


        # Display the slots
        canvas = tk.Canvas(self.admin_dashboard_window, bg="white", width=500, height=150)
        canvas.pack()
        refresh_dashboard()
        exit_button = tk.Button(self.admin_dashboard_window, text="Exit", command=self.admin_dashboard_window.destroy)
        exit_button.pack()


    def add_car(self, slot_number, car_plate):
        self.collection.update_one({"slot": slot_number},
                                   {"$set": {"status": "1", "carPlate": car_plate, "parkTime": datetime.now()}})
        messagebox.showinfo("Success", f"Car with plate number '{car_plate}' added to slot {slot_number}")

    def edit_car(self, slot_number, car_plate):
        self.collection.update_one({"slot": slot_number},
                                   {"$set": {"carPlate": car_plate}})
        messagebox.showinfo("Success", f"Car information '{car_plate}' updated for slot {slot_number}")

    def remove_car(self, slot_number):
        self.collection.update_one({"slot": slot_number},
                                   {"$set": {"status": "0", "carPlate": "", "parkTime": ""}})
        messagebox.showinfo("Success", f"Car information remove for slot {slot_number}")

    def parking_rate(self, rate):
        self.collection2.update_one({}, {"$set": {"rate": rate}})
        messagebox.showinfo("Success", f"Parking rate {rate} updated successfully.")

    def serach_car(self, search_car_plate):
        car = self.collection.find_one({"carPlate": search_car_plate})
        if car:
            #messagebox.showinfo("Search Result", f"Car with plate number '{search_car_plate}' found!")
            self.create_user_dashboard(search_car_plate)
        else:
            messagebox.showwarning("Search Result", f"'{search_car_plate}' not found.")

    def calculate_total_parked_hour(self, parkTime):
        current_time = datetime.now()
        parked_time = current_time - parkTime
        hours_parked = parked_time.total_seconds() / 3600  # Convert seconds to hours
        if hours_parked < 1:
            return 1  # If parked for less than an hour, count as 1 hour
        else:
            return int(hours_parked) + 1  # Round up to the next hour

    def calculate_parking_fees(self, total_parked_hour):
        current_rate_document = self.collection2.find_one()
        if current_rate_document:
            current_rate = current_rate_document.get("rate", 0)  # Get the current parking rate
            try:
                current_rate = float(current_rate)  # Convert the rate to float
            except ValueError:
                return "Invalid rate"

            try:
                total_parked_hour = float(total_parked_hour)  # Convert the total parked hour to float
            except ValueError:
                return "Invalid total parked hour"

            parking_fees = current_rate * total_parked_hour
            parking_fees = '{:.2f}'.format(parking_fees)  # Format to two decimal places
            return parking_fees
        else:
            return "Rate document not found"

    def payment(self, search_car_plate, user_dashboard_window):
        messagebox.showinfo("payment successful", f"Payment for '{search_car_plate}' successful")
        self.collection.update_one({"carPlate": search_car_plate},
                                   {"$set": {"status": "0", "carPlate": "", "parkTime": ""}})
        user_dashboard_window.destroy()



class Admin:
    def __init__(self, master):
        self.master = master
        self.db_uri = "mongodb://localhost:27017/"
        self.db_name = "carParkingSystem"
        self.collection_name = "adminCredential"


    def login(self):
        # Create a new window for admin login
        login_window = tk.Toplevel(self.master)
        login_window.title("Admin Login")
        login_window.geometry("400x200")  # Set the size of the window

        # Username entry
        username_label = tk.Label(login_window, text="Username:")
        username_label.pack()

        self.username_entry = tk.Entry(login_window)
        self.username_entry.pack()

        # Password entry
        password_label = tk.Label(login_window, text="Password:")
        password_label.pack()

        self.password_entry = tk.Entry(login_window, show="*")
        self.password_entry.pack()

        # Login button
        login_button = tk.Button(login_window, text="Login", command=lambda: self.authenticate(login_window))
        login_button.pack()

    def authenticate(self, login_window):
        # Connect to MongoDB and retrieve admin credentials
        client = pymongo.MongoClient(self.db_uri)
        db = client[self.db_name]
        collection = db[self.collection_name]
        admin = collection.find_one({"username": self.username_entry.get(), "password": self.password_entry.get()})

        if admin:
            self.dashboard = carParkRecord(self.master)
            login_window.destroy()
            self.dashboard.create_admin_dashboard()
        else:
            messagebox.showerror("Authentication Result", "Invalid username or password.")



class CarParkingSystemGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Car Parking System")
        self.admin = Admin(master)
        self.master.geometry("400x200")  # Set the size of the window

        # Create and pack GUI elements
        self.car_plate_label = tk.Label(self.master, text="Enter Car Plate Number:")
        self.car_plate_label.pack()

        self.car_plate_entry = tk.Entry(self.master)
        self.car_plate_entry.pack()

        self.search_button = tk.Button(self.master, text="Search", command=self.search_car)
        self.search_button.pack()

        self.admin_login_button = tk.Button(self.master, text="Login as Admin", command=self.login_as_admin)
        self.admin_login_button.pack(side=tk.TOP, anchor=tk.NE)

    def search_car(self):
        car_plate = self.car_plate_entry.get().upper().replace(" ", "")  # Convert to uppercase and remove spaces
        self.car_plate_entry.delete(0, tk.END)  # Clear the current text
        self.car_plate_entry.insert(0, car_plate)  # Insert the modified plate number
        self.dashboard = carParkRecord(self.master)
        self.dashboard.serach_car(car_plate)

    def login_as_admin(self):
        self.admin.login()



def main():
    root = tk.Tk()
    app = CarParkingSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()



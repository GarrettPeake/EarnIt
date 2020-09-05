import pickle
import time
import os
from os import path
import sys
import select
import random
import tkinter as tk
from mpyg321.mpyg321 import MPyg321Player

class Task():
    """ Represents a task a user wants to complete
    tracks multiple steps, reward decay, and progress """

    def __init__(self, description, total, reward, end_reward, decay):
        self.done = 0
        self.description = description
        self.total = total
        self.start_reward = reward
        self.reward = reward
        self.end_reward = end_reward if end_reward is not -1 else reward
        self.decay = decay if end_reward is not -1 else 0

    def is_done(self):
        """ Checks whether the user has completed this task """
        return self.done >= self.total and self.total is not -1

    def increment(self):
        """ Tracks the completion of another step and returns the associated reward """
        r = self.reward
        self.reward = max(self.reward - self.decay, self.end_reward)
        self.done += 1
        return r

class User():
    """ Class to track the name, tasks, and preferred currency of the user """

    def __init__(self, name, symbol="$"):
            self.name = name
            self.curr_sym = symbol
            self.total_earned = 0.0
            self.curr_points = 0.0
            self.total_spent = 0.0
            self.tasks = []

    def add_task(self, task):
        """ Add a new task to the user's account """
        self.tasks.append(task)

    def remove_task(self, task):
        """ Remove a task to the user's account """
        self.tasks.remove(task)

    def __str__(self):
        return (f"User: {self.name}\n"
            f"Current Balance: {self.curr_sym}{self.curr_points:.2f}\n"
            f"Totals:\n"
            f"    Earned: {self.curr_sym}{self.total_earned:.2f}\n"
            f"    Spent:  {self.curr_sym}{self.total_spent:.2f}")


class EarnIt():
    """ Class to run the EarnIt GUI """
    
    def __init__(self):
        self.timestep = -1
        self.r_choice = None
        self.alerting = False
        self.last_alert = time.time()
        self.task_elements = {}
        self.load_or_enroll()
        self.save()
        self.construct_main_window()
        self.loop()

    def save(self):
        """ Writes all program data to disk to save the current user's state"""
        pickle.dump(self.user, open(f'user.pkl', 'wb'))

    def load_or_enroll(self):
        """ Leads user through 'signup' in GUI if no file found"""
        if path.exists(f"user.pkl"):
            self.user = pickle.load(open(f"user.pkl", 'rb'))
            return
        root = tk.Tk()
        root.resizable(False, False)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.title(f"EarnIt Register New User")
        frame = tk.Frame(root, background='white')
        frame.grid(row=0, column=0, sticky=('N', 'S', 'E', 'W'))
        # Name prompt
        name_label = tk.Label(frame, text="What's your name:", background='white')
        name_label.grid(row=0, column=0, sticky=('W'), padx=10, pady=10)
        # Name Field
        name_entry = tk.Entry(frame)
        name_entry.grid(row=0, column=1, sticky=('W'), padx=10, pady=10)
        # Currency prompt
        curr_label = tk.Label(frame, text="What symbol do you use for currency:", background='white')
        curr_label.grid(row=1, column=0, sticky=('W'), padx=10, pady=10)
        # Currency Field
        curr_entry = tk.Entry(frame)
        curr_entry.grid(row=1, column=1, sticky=('N', 'S', 'E', 'W'), padx=10, pady=10)
        # Submit Button
        def set_user(self):
            self.user = User(name_entry.get(), curr_entry.get())
            root.quit()
            root.destroy()
        submit_button = tk.Button(frame, text='Register', relief='raised', command=lambda: set_user(self))
        submit_button.grid(row=2, column=1, sticky=('W'), padx=10, pady=10)
        root.mainloop()

    def construct_main_window(self):
        """ Constructs the GUI for the mainscreen """
        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.title(f"{self.user.name}'s EarnIt")
        # Construct a main frame within the root window
        self.mainframe = tk.Frame(self.root, background='white')
        self.mainframe.grid()
        # Area for general info and alert flashing
        self.top_frame = tk.Frame(self.mainframe, background='white', padx=10, pady=10)
        self.top_frame.grid(row=0, column=0, sticky=('N', 'S', 'E', 'W'))
        # Area for list of tasks with actions
        self.mid_frame = tk.Frame(self.mainframe, background='white', padx=10, pady=10)
        self.mid_frame.grid(row=1, column=0, sticky=('N', 'S', 'E', 'W'))
        # Area for other stuff
        self.bottom_frame = tk.Frame(self.mainframe, background='white', padx=10, pady=10)
        self.bottom_frame.grid(row=2, column=0, sticky=('N', 'S', 'E', 'W'))
        # Do the initial configuration of the 3 frames
        self.configure_top_frame()
        self.configure_mid_frame()
        self.configure_bottom_frame()

    def configure_top_frame(self):
        """ Adds all of the necessary content to the top frame each cycle """
        # Display the users details
        self.user_info = tk.Label(self.top_frame, text=str(self.user), justify=tk.LEFT, background='white', padx=10, pady=10)
        self.user_info.grid(row=0, column=0, sticky=('W'))
        # Set up and area to display an alert
        self.alert_box = tk.Label(self.top_frame, background='white', padx=10, pady=10)
        self.alert_box.grid(row=0, column=1, sticky=('E'))
        # Setup box to edit the time between alerts
        self.time_set_frame = tk.Frame(self.top_frame, background='white', padx=10, pady=10)
        self.time_set_frame.grid(row=0, column=2, sticky=('N', 'S', 'E', 'W'))
        timestep_label = tk.Label(self.time_set_frame, text='Set minutes between alerts:', justify='center', background='white', padx=10, pady=10)
        timestep_label.grid(row=0, column=0, sticky=('W'))
        timestep_entry = tk.Entry(self.time_set_frame)
        timestep_entry.grid(row=1, column=0, sticky=('W'), padx=10, pady=10)
        def set_timestep():
            try:
                self.timestep = int(timestep_entry.get()) * 60
            except:
                pass
        submit_button = tk.Button(self.time_set_frame, text='Set', relief='raised', command=lambda: set_timestep())
        submit_button.grid(row=2, column=0, padx=2, pady=2)
    
    def update_top_frame(self):
        """ Updates all of the information contained within the top frame """
        self.user_info['text'] = str(self.user)
        if time.time() - self.last_alert > self.timestep and self.timestep > -1 and not self.alerting:
            # Bring the window to the front
            self.root.lift()
            # Play an alert sound
            player.play_song("alert.mp3")
            # Choose a random task
            self.r_choice = random.choice(self.user.tasks)
            self.alert_box['text'] = 'Time to do something!!\nRandom choice highlighted\nDoing any task will clear alert'
            self.alerting = True
        if not self.alerting and self.timestep is not -1:
            # Countdown if we have alerts scheduled but we aren't currently alerting
            self.alert_box['background'] = 'white'
            t = self.timestep-(time.time()-self.last_alert)
            self.alert_box['text'] = f'Next alert in:\n{str(int(t/3600)).zfill(2)}:{str(int(t/60)).zfill(2)}:{str(int(t%60)).zfill(2)}'
        if self.alerting:
            # Flash if alerting
            self.alert_box['background'] = 'white' if int(time.time()) % 2 == 0 else 'red'
        if self.timestep is -1:
            # Clear if alerts are disabled
            self.alert_box['background'] = 'white'
            self.alert_box['text'] = 'Alerts Disabled'

    def configure_mid_frame(self):
        """ Adds all of the necessary content to the middle frame each cycle """
        increment_button = tk.Button(self.mid_frame, text='Add New Task', relief='raised', command=lambda: self.add_task())
        increment_button.grid(row=0, column=0, padx=2, pady=2, sticky=('N', 'S', 'E', 'W'))

    def update_mid_frame(self):
        """ Updates all of the information contained within the mid frame """
        for task in self.user.tasks:
            if task in self.task_elements.keys():
                self.update_task_elements(task, self.task_elements[task])
            else:
                self.task_elements[task] = self.create_task_elements(task)

    def create_task_elements(self, task):
        """ Create an element representation of a task """
        # Create a frame to encompass the entire task
        frame = tk.Frame(self.mid_frame, background='white', padx=5, pady=5, highlightbackground='black', highlightthickness=1)
        frame.grid(sticky=('N', 'S', 'E', 'W'), pady=3)
        # Create the text
        text = tk.Label(frame, text='', background='white', padx=2, pady=20, width=60)
        text.grid(row=0, column=0, sticky=('N', 'S', 'E', 'W'))
        # Create a frame for the buttons
        button_frame = tk.Frame(frame, background='white', padx=5, pady=5)
        button_frame.grid(row=0, column=1)
        # Place both button
        increment_button = tk.Button(button_frame, text='Complete', relief='raised', command=lambda: self.increment(task))
        increment_button.grid(row=0, column=0, padx=2, pady=2)
        edit_button = tk.Button(button_frame, text='Edit Task', relief='raised', command=lambda: self.edit(task))
        edit_button.grid(row=1, column=0, padx=2, pady=2)
        return {'frame': frame, 'text': text, 'increment': increment_button, 'edit': edit_button}

    def increment(self, task):
        """ When the done button is pressed on task this updates it and gives the user the reward """
        if self.alerting:
            self.last_alert = time.time()
            self.alerting = False
            self.r_choice = None
        reward = task.increment()
        self.user.curr_points += reward
        self.user.total_earned += reward

    def edit(self, task):
        """ Opens an editor when a task is clicked to be edited """
        window = tk.Tk()
        window.resizable(False, False)
        window.title(f"Edit Task {task.description}")
        # Construct a main frame within the root window
        frame = tk.Frame(window, background='white')
        frame.grid()
        # description, total, reward, end_reward, decay
        # Description label
        description_label = tk.Label(frame, text="Task Description: ", background='white')
        description_label.grid(row=0, column=0, sticky=('W'), padx=10, pady=10)
        # Description entry
        description_entry = tk.Entry(frame)
        description_entry.insert(0, task.description)
        description_entry.grid(row=0, column=1, sticky=('W'), padx=10, pady=10)
        # Total label
        total_label = tk.Label(frame, text="Maximum task repetitions -1 for infinite: ", background='white')
        total_label.grid(row=1, column=0, sticky=('W'), padx=10, pady=10)
        # Total entry
        total_entry = tk.Entry(frame)
        total_entry.insert(0, f"{task.total:.2f}")
        total_entry.grid(row=1, column=1, sticky=('W'), padx=10, pady=10)
        # Reward label
        reward_label = tk.Label(frame, text="Reward per repetition: ", background='white')
        reward_label.grid(row=2, column=0, sticky=('W'), padx=10, pady=10)
        # Reward entry
        reward_entry = tk.Entry(frame)
        reward_entry.insert(0, f"{task.reward:.2f}")
        reward_entry.grid(row=2, column=1, sticky=('W'), padx=10, pady=10)
        # Decay Description
        decay_desc = tk.Label(frame, text=f"Following settings are for decay meaning you receive less rewards the more you do a task\n"
                                          f"Decay starts after you save this task and ignores previous completions", 
                                          background='white', justify='left')
        decay_desc.grid(row=3, sticky=('W'), padx=10, pady=10)
        # Min Reward label
        end_reward_label = tk.Label(frame, text="Minimum Reward per repetition (-1 for no decay): ", background='white')
        end_reward_label.grid(row=4, column=0, sticky=('W'), padx=10, pady=10)
        # Min Reward entry
        end_reward_entry = tk.Entry(frame)
        end_reward_entry.insert(0, f"{task.end_reward:.2f}")
        end_reward_entry.grid(row=4, column=1, sticky=('W'), padx=10, pady=10)
        # Steps label
        steps_label = tk.Label(frame, text="Steps until minimum reached (-1 for no decay): ", background='white')
        steps_label.grid(row=5, column=0, sticky=('W'), padx=10, pady=10)
        # Decay Steps entry
        steps_entry = tk.Entry(frame)
        steps_entry.insert(0, f"{int((task.reward - task.end_reward) / task.decay)}")
        steps_entry.grid(row=5, column=1, sticky=('W'), padx=10, pady=10)
        def delete(self, task):
            self.task_elements[task]['frame'].destroy()
            self.user.remove_task(task)
            window.quit()
            window.destroy()
        def save(self, task):
            try:
                task.description = description_entry.get()
                task.total = int(total_entry.get())
                task.reward = float(reward_entry.get())
                task.start_reward = task.reward + task.decay * task.done
                task.end_reward = float(end_reward_entry.get()) if end_reward_entry.get() is not -1 else task.reward
                task.decay = (task.reward - task.end_reward)/(int(steps_entry.get()) if int(steps_entry.get()) is not 0 else 1)
                window.quit()
                window.destroy()
            except:
                pass
        def cancel():
            window.quit()
            window.destroy()
        # Delete button
        delete_button = tk.Button(frame, text='Delete Task', relief='raised', command=lambda: delete(self, task))
        delete_button.grid(row=6, column=0, padx=2, pady=2)
        # Save
        save_button = tk.Button(frame, text='Save Task', relief='raised', command=lambda: save(self, task))
        save_button.grid(row=6, column=1, padx=2, pady=2)
        # Cancel
        cancel_button = tk.Button(frame, text='Cancel Edit', relief='raised', command=lambda: cancel())
        cancel_button.grid(row=6, column=2, padx=2, pady=2)
        window.mainloop()


    def update_task_elements(self, task, elements):
        """ Update a preexisting task block """
        sym = self.user.curr_sym
        str_line_1 = f"{task.description} completed {task.done} times for a total of {sym}{sum([(i+1)*task.decay + task.reward for i in range(task.done)]):.2f}"
        str_line_2_1 = f"Reward will decrease from {sym}{task.start_reward:.2f} to {sym}{task.end_reward:.2f} and next reward is {sym}{task.reward:3.2f}"
        str_line_2_2 = f"Reward: {sym}{task.reward:3.2f}"
        self.task_elements[task]['text']['text'] = str_line_1 + "\n" + (str_line_2_1 if task.end_reward != -1 else str_line_2_2)
        if task is self.r_choice:
            self.task_elements[task]['frame']['background'] = 'red'
            self.task_elements[task]['text']['background'] = 'red'
        else:
            self.task_elements[task]['frame']['background'] = 'white'
            self.task_elements[task]['text']['background'] = 'white'

    def configure_bottom_frame(self):
        """ Adds all of the necessary content to the bottom frame each cycle """
        spend_label = tk.Label(self.bottom_frame, text='Record a purchase you\'ve made:', justify=tk.LEFT, background='white', padx=10, pady=10)
        spend_label.grid(row=0, column=0, sticky=('W'))
        spend_entry = tk.Entry(self.bottom_frame)
        spend_entry.grid(row=0, column=1, sticky=('W'), padx=10, pady=10)
        def spend():
            try:
                self.user.total_spent += float(spend_entry.get())
                self.user.curr_points -= float(spend_entry.get())
            except:
                pass
        submit_button = tk.Button(self.bottom_frame, text='Submit Expenditure', relief='raised', command=lambda: spend())
        submit_button.grid(row=0, column=2, padx=2, pady=2)

    def update_bottom_frame(self):
        """ Updates all of the information contained within the bottom frame """
        pass

    def add_task(self):
        """ Throw in a blank task and open editor on it """
        t = Task('', -1, 0.0, -1, -1)
        self.user.add_task(t)
        self.edit(t)

    def loop(self):
        """ Loop that runs the program """
        last_save = time.time()
        while True:
            self.update_top_frame()
            self.update_mid_frame()
            self.update_bottom_frame()
            self.root.update_idletasks()
            self.root.update()
            if time.time() - last_save > 5:
                # Save the user's data every 5 seconds
                self.save()
                last_save = time.time()
    

if __name__ == '__main__':
    player = MPyg321Player()
    program = EarnIt()
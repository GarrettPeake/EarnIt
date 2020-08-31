import pickle
import time
import os
import sys
import select
import random

class Task():
    """ Represents a task a user wants to complete
    tracks multiple steps, reward decay, and progress """

    def __init__(self, total, amount_per, name, reward, min_reward, decay_steps):
        self.total = total
        self.done = 0
        self.name = name
        self.amount = amount_per
        self.reward = reward
        self.min_reward = min_reward
        self.decay = (reward - min_reward) / decay_steps

    def is_done(self):
        """ Checks whether the user has completed this task """
        return self.done >= self.total and self.total is not -1

    def increment(self):
        """ Tracks the completion of another step and returns the associated reward or -1 if the task is complete"""
        r = self.reward
        self.reward = max(self.reward - self.decay, self.min_reward)
        self.done += 1
        return -1 if self.is_done() else r


class User():

    def __init__(self, name, symbol="$"):
            self.name = name
            self.curr_sym = symbol
            self.points = 0
            self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def print_task(self, task):
        print(f'You are doing {task.amount} {task.name} {f"a total of {task.total} times" if task.total != -1 else "repeatedly"}'\
        f' for a reward of {self.curr_sym}{task.reward:.2f} that decreases by {self.curr_sym}'\
        f'{task.decay:.2f} each time you do it until you\'re earning {self.curr_sym}{task.min_reward:.2f}'\
        f' each time')

    def print_task_progress(self, task):
        print(f'You have done {task.amount} {task.name} {task.done} times and earned'\
        f' a total of {self.curr_sym}{sum([(i+1)*task.decay + task.reward for i in range(task.done)]):.2f}'\
        f' from doing it')

    def print_tasks(self):
        for i in self.tasks:
            self.print_task(i)
            print()

    def print_progresses(self):
        for i in self.tasks:
            self.print_task_progress(i)
            print()

    def __str__(self):
        return f"User: {self.name}\nCurrent Balance: {self.curr_sym}{self.points:.2f}"

class EarnIt():
    """ Class to run the entire EarnIt Program """
    
    def __init__(self):
        os.system('clear')
        self.timestep = -1
        self.last_alert = 0
        if self.has_save():
            self.user = pickle.load(open(self.has_save(), 'rb'))
        else:
            self.user = self.construct_from_cdl()
        t1 = Task(5, 5, "Jacks", 2.0, 1.0, 5)
        t2 = Task(-1, 5, "Johns", 3.0, 1.0, 5)
        self.user.add_task(t1)
        self.user.add_task(t2)
        self.loop()

    def has_save(self):
        """ Discovers any save files and returns their names"""
        return False

    def save(self):
        """ Writes all program data to disk to save the current user's state"""
        pickle.dump(self.user, open(f'{self.user.name}.pkl', 'wb'))

    def construct_from_cdl(self):
        """ Leads user through 'signup' on CDL and adds tasks """
        print("Hi! Welcome to EarnIt: an easy way to reward yourself for completing your goals")
        print("We just need a name to get started so...")
        name = input("What should I call you? ")
        currency = input("Oh and also, what symbol do you want to use for currency? ")
        return User(name, currency)

    def alert_if_ready(self):
        """ Alerts the user if the timestep has passed """
        if time.time() - self.last_alert > self.timestep and self.timestep is not -1:
            print("Yoohoo it's time for you to do something!")
            r = input("Do you:\n\t1: want a random tasks\n\t2: want to select one\nEnter: ") is '1'
            t = None
            if r:
                t = random.choice(self.user.tasks)
            else:
                for i, t in enumerate(self.user.tasks):
                    print(f"{i + 1}: {t.name}")
                t = self.user.tasks[int(input("Enter the number of the task you'd like to complete: ")) - 1]
            print(f"Your task is to do {t.amount} {t.name}, you've done this task {t.done} time so far")
            input("Press enter once you've completed your task")
            reward = t.increment()
            if t.is_done():
                self.user.tasks.remove(t)
            if reward > 0:
                self.user.points += reward
                print(f"Congrats you earned {self.user.curr_sym}{reward:.2f} to spend how you wish")
                print("Balance updated!")
                time.sleep(1)
            self.last_alert = time.time()

    def add_task(self):
        """ Construct a new task from the commandline and add it to the user """
        u = "\033[4m{}\033[0m"
        print("Let's walk you through adding a new task")
        print("Enter the information to replace the underlined info:")
        print(f'I want to do {u.format("5")} {u.format("Jumping Jacks")} a total of {u.format("15")}'\
        f' times with a reward starting at {self.user.curr_sym}{u.format("4.50")} and'
        f' decreasing over the first {u.format("8")} steps to a minimum reward of {self.user.curr_sym}{u.format("3.50")}')
        amount_per = int(input(" 1, number per completion: "))
        name = input(" 2, name of the task: ")
        total = int(input(" 3, how many times you want to do it: "))
        reward = float(input(" 4, starting reward: "))
        decay_steps = int(input(" 5, number of decay steps: "))
        min_reward = float(input(" 6, minimum reward: "))
        t = Task(total, amount_per, name, reward, min_reward, decay_steps)
        print()
        self.user.print_task(t)
        if input("\nDo you want to add this task? (y/n) ") == 'y':
            self.user.add_task(t)

    def remove_task(self):
        """ Remove a specific task from a user """
        print("Warning this will remove a task and reset your progress")
        if input("Are you sure you want to continue? (y/n) ") is "n": return
        print("Here are all of your tasks:")
        for i, t in enumerate(self.user.tasks):
            print(f"{i + 1}: {t.name}")
        del self.user.tasks[int(input("Enter the number of the task you'd like to remove: ")) - 1]

    def increment(self):
        """ Update progress on a certain task """
        print("Here are all of your current tasks:")
        for i, t in enumerate(self.user.tasks):
            print(f"{i + 1}: {t.name}")
        t = self.user.tasks[int(input("Enter the number of the task you did: ")) - 1]
        reward = t.increment()
        if t.is_done():
            self.user.tasks.remove(t)
        if reward > 0:
            self.user.points += reward
            print(f"Congrats you earned {self.user.curr_sym}{reward:.2f} to spend how you wish")
            print("Balance updated!")
            time.sleep(1)

    def spend(self):
        """ Remove money from the user """
        print("Glad you're treating youself, and remember, embezzlement is illegal so don't lie")
        self.user.points -= min(0, float(input("How much did you spend? ")))
        print("Balance updated")
        time.sleep(1)

    def set_timestep(self):
        """ Set the timestep between alerts to do something """
        print("So you want us to annoy you? Sounds good! how often?")
        self.timestep = float(input("Enter time between alerts in minutes (-1 to turn alerts off): ")) * 60
        self.last_alert = time.time()

    def show_tasks(self):
        """ Show all of the users current tasks """
        print("Here are all of your tasks:")
        self.user.print_tasks()
        input("Press enter to return to the menu...")

    def show_progress(self):
        """ Displays the users goal progress and EarnIt info by task """
        self.user.print_progresses()
        input("Press enter to return to the menu...")

    def get_menu_selection(self):
        """ Prints a menu for the user to begin using the program """
        options = {
            "Add a new task": self.add_task,
            "Remove a task": self.remove_task,
            "I just completed a task": self.increment,
            "I just spent points": self.spend,
            "Show me my tasks": self.show_tasks,
            "Show me my performance": self.show_progress,
            "Configure alerts": self.set_timestep,
        }
        for i, o in enumerate(options.keys()):
            print(f'{i+1}: {o}')
        print("Enter selection number: ", end="", flush=True)
        i, o, e = select.select([sys.stdin], [], [], 5) # Add a timeout to the input so we don't block the alerts
        if (i):
            return options[list(options.keys())[int(sys.stdin.readline().strip()) - 1]]
        else:
            return lambda a=1 : a

    def loop(self):
        """ Loop that runs the program """
        while True:
            try:
                os.system('clear')
                print(self.user, "\n")
                selection = self.get_menu_selection()
                os.system('clear')
                selection()
                self.alert_if_ready()
                self.save()
            except:
                os.system('clear')
                print("Looks like you encountered an error, likely typed in a number wrong")
                print("If you think this is in error, please report it on the repository page")
                input("Press enter to return to the menu...")
    

if __name__ == '__main__':
    program = EarnIt()
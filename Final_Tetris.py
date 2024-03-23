# Import Tkinter library for GUI
import tkinter as tk
# Import random module for generating random values
import random
# Import threading utilities
from threading import Lock, Thread, Event
# Import CSV module for handling CSV files
import csv
# Import pygame for handling music
import pygame
# Import messagebox module from Tkinter for displaying messages
from tkinter import messagebox

COLORS = ['gray', 'lightgreen', 'pink', 'blue', 'orange',
          'purple']         # List of colors for tetrominos


class Tetris():
    # Height of the game field
    FIELD_HEIGHT = 20
    # Width of the game field
    FIELD_WIDTH = 10
    # Scores for eliminating lines
    # Tetrominos represented as a list of coordinates
    SCORE_PER_ELIMINATED_LINES = (0, 40, 100, 300, 1200)
    TETROMINOS = [
        [(0, 0), (0, 1), (1, 0), (1, 1)],                                   # O
        [(0, 0), (0, 1), (1, 1), (2, 1)],                                   # L
        [(0, 1), (1, 1), (2, 1), (2, 0)],                                   # J
        [(0, 1), (1, 0), (1, 1), (2, 0)],                                   # Z
        [(0, 1), (1, 0), (1, 1), (2, 1)],                                   # T
        [(0, 0), (1, 0), (1, 1), (2, 1)],                                   # S
        [(0, 1), (1, 1), (2, 1), (3, 1)],                                   # I
    ]

    # defining the initializing function
    def __init__(self):
        self.field = [[0 for c in range(Tetris.FIELD_WIDTH)]
                      for r in range(Tetris.FIELD_HEIGHT)]                  # Initialize game field
        # Initialize score
        self.score = 0
        # Initialize level
        self.level = 0
        # Initialize total lines eliminated
        self.total_lines_eliminated = 0
        # Initialize game over state
        self.game_over = False
        # Create lock for thread safety
        self.move_lock = Lock()
        # Reset tetromino to start the game
        self.reset_tetromino()

    # defining the reset_tetromino
    def reset_tetromino(self):
        # Choose a random tetromino
        self.tetromino = random.choice(Tetris.TETROMINOS)[:]
        # Choose a random color for tetromino
        self.tetromino_color = random.randint(1, len(COLORS)-1)
        # Set initial offset for tetromino
        self.tetromino_offset = [-2, Tetris.FIELD_WIDTH//2]
        self.game_over = any(not self.is_cell_free(r, c)
                             for (r, c) in self.get_tetromino_coords())     # Check if game over

    # defining the get_tetromino_coords
    def get_tetromino_coords(self):
        # Get coordinates of current tetromino
        return [(r+self.tetromino_offset[0], c + self.tetromino_offset[1]) for (r, c) in self.tetromino]

    def apply_tetromino(self):
        # Apply tetromino to game field
        for (r, c) in self.get_tetromino_coords():
            self.field[r][c] = self.tetromino_color
        # Get updated game field after eliminating lines
        new_field = [row for row in self.field if any(
            tile == 0 for tile in row)]
        # Calculate lines eliminated
        lines_eliminated = len(self.field)-len(new_field)
        # Update total lines eliminated
        self.total_lines_eliminated += lines_eliminated
        # Update game field
        self.field = [
            [0]*Tetris.FIELD_WIDTH for x in range(lines_eliminated)] + new_field
        # Update score
        self.score += Tetris.SCORE_PER_ELIMINATED_LINES[lines_eliminated] * (
            self.level + 1)
        # Update level
        self.level = self.total_lines_eliminated // 5
        # Reset tetromino for next move
        self.reset_tetromino()

    # defining the get_colorfunction
    def get_color(self, r, c):
        # Get color of cell
        return self.tetromino_color if (r, c) in self.get_tetromino_coords() else self.field[r][c]

    # defining the is_cell_free function
    def is_cell_free(self, r, c):
        # Check if cell is free
        return r < Tetris.FIELD_HEIGHT and 0 <= c < Tetris.FIELD_WIDTH and (r < 0 or self.field[r][c] == 0)

    # defining the move function
    def move(self, dr, dc):
        # Acquire lock for thread safety
        with self.move_lock:
            # Check if game over
            if self.game_over:
                return
            # Check if move is valid
            if all(self.is_cell_free(r + dr, c + dc) for (r, c) in self.get_tetromino_coords()):
                # Update tetromino offset
                self.tetromino_offset = [
                    self.tetromino_offset[0] + dr, self.tetromino_offset[1] + dc]
            # If move is downwards
            elif dr == 1 and dc == 0:
                # Check if game over
                self.game_over = any(r < 0 for (
                    r, c) in self.get_tetromino_coords())
                # If game is not over
                if not self.game_over:
                    # Apply tetromino to game field
                    self.apply_tetromino()

    # defining the rotate function
    def rotate(self):
        # Acquire lock for thread safety
        with self.move_lock:
            # If game over
            if self.game_over:
                # Reset game
                self.__init__()
                return

            # Get y coordinates of tetromino
            ys = [r for (r, c) in self.tetromino]
            # Get x coordinates of tetromino
            xs = [c for (r, c) in self.tetromino]
            # Calculate size of tetromino
            size = max(max(ys) - min(ys), max(xs)-min(xs))
            # Calculate rotated tetromino
            rotated_tetromino = [(c, size-r) for (r, c) in self.tetromino]
            # Copy current offset
            wallkick_offset = self.tetromino_offset[:]
            tetromino_coord = [(r+wallkick_offset[0], c + wallkick_offset[1])
                               for (r, c) in rotated_tetromino]  # Get coordinates of rotated tetromino
            # Get minimum x coordinate
            min_x = min(c for r, c in tetromino_coord)
            # Get maximum x coordinate
            max_x = max(c for r, c in tetromino_coord)
            # Get maximum y coordinate
            max_y = max(r for r, c in tetromino_coord)
            # Adjust x offset
            wallkick_offset[1] -= min(0, min_x)
            # Adjust x offset
            wallkick_offset[1] += min(0, Tetris.FIELD_WIDTH - (1 + max_x))
            # Adjust y offset
            wallkick_offset[0] += min(0, Tetris.FIELD_HEIGHT - (1 + max_y))

            tetromino_coord = [(r+wallkick_offset[0], c + wallkick_offset[1])
                               for (r, c) in rotated_tetromino]  # Get final coordinates
            # Check if move is valid
            if all(self.is_cell_free(r, c) for (r, c) in tetromino_coord):
                # Update tetromino and offset
                self.tetromino, self.tetromino_offset = rotated_tetromino, wallkick_offset


# Define a class named Application inheriting from tk.Frame
class Application(tk.Frame):
    # Define the initialization method of the class
    def __init__(self, master=None, manager=None):
        # Call the initialization method of the superclass (tk.Frame)
        super().__init__(master)
        # Create an instance of the Tetris class
        self.tetris = Tetris()
        # Initialize the manager attribute with the provided manager parameter
        self.manager = manager
        # Use the pack geometry manager to organize the widgets in the window
        self.pack()
        # Call the create_widgets method to create GUI elements
        self.create_widgets()
        # Call the update_clock method to start the game clock
        self.update_clock()

    # Define a method to get the current score
    def get_current_score(self):
        # Return the score attribute of the Tetris instance
        return self.tetris.score

    # Define a method to update the game clock
    def update_clock(self):
        # Check if the game is not paused
        if not self.manager.pause_event.is_set():
            # Move the tetromino down by one unit
            self.tetris.move(1, 0)
            # Update the GUI
            self.update()
        # Schedule the next clock update
        self.master.after(
            int(1000*(0.66**self.tetris.level)), self.update_clock)
        # Check if the game is paused
        if self.manager.game_paused:
            # Schedule another clock update after 100 milliseconds
            self.after(100, self.update_clock)
            # Exit the method
            return

    # Define a method to create GUI widgets
    def create_widgets(self):
        # Define the size of a tetromino piece
        PIECE_SIZE = 30
        self.canvas = tk.Canvas(self, height=PIECE_SIZE*self.tetris.FIELD_HEIGHT, width=PIECE_SIZE *
                                self.tetris.FIELD_WIDTH, bg="black", bd=0)    # Create a canvas widget
        # Bind left arrow key to move left
        self.canvas.bind('<Left>', lambda _: (
            self.tetris.move(0, -1), self.update()))
        # Bind right arrow key to move right
        self.canvas.bind('<Right>', lambda _: (
            self.tetris.move(0, 1), self.update()))
        # Bind down arrow key to move down
        self.canvas.bind('<Down>', lambda _: (
            self.tetris.move(1, 0), self.update()))
        # Bind up arrow key to rotate tetromino
        self.canvas.bind('<Up>', lambda _: (
            self.tetris.rotate(), self.update()))
        # Bind 'p' key to toggle pause
        self.canvas.bind('<p>', lambda _: self.manager.toggle_pause())
        # Bind space key to instant drop
        self.canvas.bind('<space>', lambda _: self.instant_drop())
        # Bind 'r' key to restart game
        self.canvas.bind('<r>', lambda _: self.restart_game())
        # Set focus to the canvas widget
        self.canvas.focus_set()
        self.rectangles = [                                                                               # Create rectangles representing the game field
            self.canvas.create_rectangle(
                c*PIECE_SIZE, r*PIECE_SIZE, (c+1)*PIECE_SIZE, (r+1)*PIECE_SIZE)
            for r in range(self.tetris.FIELD_HEIGHT) for c in range(self.tetris.FIELD_WIDTH)
        ]
        # Pack the canvas widget to the left side of the window
        self.canvas.pack(side="left")
        # Create a label widget for status message
        self.status_msg = tk.Label(
            self, anchor='w', width=11, font=("Courier", 24))
        # Pack the status message label to the top of the window
        self.status_msg.pack(side="top")
        self.game_over_msg = tk.Label(self, anchor='w', width=11, font=(
            "Courier", 24), fg='red')         # Create a label widget for game over message
        # Pack the game over message label to the top of the window
        self.game_over_msg.pack(side="top")
        self.instructions_msg = tk.Label(self, anchor='w', font=(
            "Courier", 12), fg='black', text="PRESS\nq to quit the game\np to pause the game\nm to mute the music\nr to restart the game\nspace to drop the block instantly\nup key to change the shape of block")  # Create a label widget for instructions
        # Pack the instructions label to the top of the window with padding
        self.instructions_msg.pack(side="top", anchor='w', padx=5, pady=(5, 0))
        # Bind 'q' key to exit and save game
        self.canvas.bind('<q>', lambda _: self.manager.exit_and_save())
        # Bind 'm' key to toggle music
        self.canvas.bind(
            '<m>', lambda _: self.manager.music_player.toggle_music())
        # Set focus to the canvas widget
        self.canvas.focus_set()

    # Define a method to restart the game
    def restart_game(self):
        # Create a new instance of Tetris
        self.tetris = Tetris()
        # Update the GUI to reflect the new game state
        self.update()

    # Define a method to update the GUI
    def update(self):
        # Iterate over the rectangles representing the game field
        for i, _id in enumerate(self.rectangles):
            # Get the color of the current cell
            color_num = self.tetris.get_color(
                i//self.tetris.FIELD_WIDTH, i % self.tetris.FIELD_WIDTH)
            # Update the color of the rectangle
            self.canvas.itemconfig(_id, fill=COLORS[color_num])

        self.status_msg['text'] = "Score: {}\nLevel: {}".format(
            self.tetris.score, self.tetris.level)     # Update the status message
        # Update the game over message
        self.game_over_msg['text'] = "GAME OVER.\nPress UP\nto reset" if self.tetris.game_over else ""

    # Define a method to perform an instant drop
    def instant_drop(self):
        # Loop until the game is paused
        while not self.manager.pause_event.is_set():
            # Check if the game is over
            if self.tetris.game_over:
                # Exit the loop
                break
            # Check if all cells below the tetromino are free
            if all(self.tetris.is_cell_free(r + 1, c) for (r, c) in self.tetris.get_tetromino_coords()):
                # Move the tetromino down by one unit
                self.tetris.move(1, 0)
                # Update the GUI
                self.update()
            else:
                # Exit the loop
                break


# creating a class name musicplayer
class MusicPlayer:
    def __init__(self, music_file):
        # Initialize pygame mixer
        pygame.mixer.init()
        # Set the music file
        self.music_file = "Tetris.mp3"
        # Initialize playing state
        self.is_playing = False

    # defining the start_music function
    def start_music(self):
        # Load music file
        pygame.mixer.music.load(self.music_file)
        # Play music indefinitely
        pygame.mixer.music.play(-1)
        # Update playing state
        self.is_playing = True

    # defining the stop_music function
    def stop_music(self):
        # Stop music playback
        pygame.mixer.music.stop()
        # Update playing state
        self.is_playing = False

    # defining the toggle_music function
    def toggle_music(self):
        # if the condition is true
        if self.is_playing:
            # If music is playing, stop it
            self.stop_music()
        # if the condition is false
        else:
            # If music is not playing, start it
            self.start_music()


# creating a class name threadmanager
class ThreadManager:
    # defining the initialization function
    def __init__(self):
        # Initialize player name
        self.player_name = None
        # Initialize application instance
        self.app = None
        # Initialize score data list
        self.score_data = []
        # Initialize game running state
        self.game_running = False
        # Initialize game paused state
        self.game_paused = False
        # Initialize thread lock
        self.thread_lock = Lock()
        # Initialize game thread
        self.game_thread = None
        # Initialize event for name entry
        self.name_entered = Event()
        # Initialize music player
        self.music_player = MusicPlayer('Tetris.mp3')
        # Create threads for various tasks
        self.create_threads()
        # Initialize event for pausing the game
        self.pause_event = Event()
        # Set the pause event to allow starting the game
        self.pause_event.set()

    # defining the create_threads function
    def create_threads(self):
        # Thread for getting player name
        self.thread1 = Thread(target=self.get_player_name)
        # Thread for starting the game
        self.thread2 = Thread(target=self.start_game)
        # Thread for toggling pause
        self.thread3 = Thread(target=self.toggle_pause)
        # Thread for starting music
        self.thread4 = Thread(target=self.music_player.start_music)

    def get_player_name(self):
        # Create Tkinter root window
        root = tk.Tk()
        # Set window title
        root.title("Tetris")
        # Center the window on the screen
        self.center_window(root, 300, 150)
        # Create label for name entry
        label = tk.Label(root, text="Enter your name:")
        # Pack the label into the window
        label.pack()
        # Create entry widget for name input
        entry = tk.Entry(root)
        # Pack the entry widget into the window
        entry.pack()
        button = tk.Button(root, text="Submit", command=lambda: self.submit_name(
            root, entry))            # Create submit button
        # Pack the button into the window
        button.pack()
        # Start the Tkinter event loop for name entry
        root.mainloop()

    # defining the submit_name function
    def submit_name(self, root, entry):
        # Get entered name
        entered_name = entry.get().strip()
        # Use entered name or set to Guest
        self.player_name = entered_name if entered_name else "Guest"
        # Destroy the name entry window
        root.destroy()
        # Set event indicating name entry is done
        self.name_entered.set()

    # defining the start_name function
    def start_game(self):
        # Wait for player name to be entered
        self.name_entered.wait()
        # Set game running state to True
        self.game_running = True
        # Create Tkinter root window for the game
        root = tk.Tk()
        # Create instance of Application class
        self.app = Application(master=root, manager=self)
        # Start the Tkinter event loop for the game
        self.app.mainloop()
        # Set game running state to False when game ends
        self.game_running = False

    # defining the toggle_pause function
    def toggle_pause(self):
        # Check if game is not paused
        if self.pause_event.is_set():
            # Clear pause event to pause the game
            self.pause_event.clear()
            # Toggle music playback
            self.music_player.toggle_music()
        # the if condition is wrong then it will run else
        else:
            # Set pause event to resume the game
            self.pause_event.set()
            # Toggle music playback
            self.music_player.toggle_music()
            messagebox.showinfo(
                "Game Paused", "Game Paused. Close the messagebox and press 'p' again to continue.")      # Display pause message

    def save_score_data(self, score):  # defining the save_score_data function
        # Add player name and score to score data list
        self.score_data.append((self.player_name, score))
        # Open CSV file for appending
        with open('scores.csv', 'a', newline='') as file:
            # Create CSV writer
            writer = csv.writer(file)
            # Write player name and score to CSV
            writer.writerow((self.player_name, score))

    # defining the exit_and_save function
    def exit_and_save(self):
        # Check if game is running
        if self.game_running:
            # Get current score
            current_score = self.app.get_current_score()
            # Save current score
            self.save_score_data(current_score)
            # Set game running state to False
            self.game_running = False
            # Destroy the game window
            self.app.master.after(0, self.app.master.destroy)

    # defining the run function
    def run(self):
        # Start thread for getting player name
        self.thread1.start()
        # Start thread for starting the game
        self.thread2.start()
        # Start thread for toggling pause
        self.thread3.start()
        # Start thread for starting music
        self.thread4.start()

    # defining the center_window function
    def center_window(self, window, window_width, window_height):
        # Get screen width
        screen_width = window.winfo_screenwidth()
        # Get screen height
        screen_height = window.winfo_screenheight()
        # Calculate x-coordinate for centering
        x = (screen_width // 2) - (window_width // 2)
        # Calculate y-coordinate for centering
        y = (screen_height // 2) - (window_height // 2)
        # Set window geometry
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")


# check if the script is being run directly
if __name__ == "__main__":
    # calling the threadmanager
    manager = ThreadManager()
    # will call the run method
    manager.run()

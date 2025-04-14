import pygame
import random
import numpy as np
from collections import deque
import time

# Initialize pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# Tetromino colors
COLORS = {
    "I": CYAN,
    "J": BLUE,
    "L": ORANGE,
    "O": YELLOW,
    "S": GREEN,
    "T": PURPLE,
    "Z": RED
}

# Tetromino shapes
SHAPES = {
    "I": [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ],
    "J": [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 0]
    ],
    "L": [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0]
    ],
    "O": [
        [1, 1],
        [1, 1]
    ],
    "S": [
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 0]
    ],
    "T": [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 0]
    ],
    "Z": [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 0]
    ]
}

# Game constants
CELL_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE * 2 + 300  # Extra space for UI and next pieces
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE + 100
FPS = 60

class Tetromino:
    def __init__(self, shape_name, x=None, y=0, rotation=0):
        self.shape_name = shape_name
        self.shape = SHAPES[shape_name]
        self.color = COLORS[shape_name]
        self.rotation = rotation
        # Default starting position (center of the top row)
        if x is None:
            self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        else:
            self.x = x
        self.y = y
    
    def rotate(self):
        # Create a rotated version of the shape (90 degrees clockwise)
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for r in range(rows):
            for c in range(cols):
                rotated[c][rows - 1 - r] = self.shape[r][c]
        
        return rotated
    
    def get_rotated_shape(self, rotations=1):
        # Get the shape after the specified number of rotations
        shape = [row[:] for row in self.shape]  # Make a copy
        for _ in range(rotations % 4):
            rows = len(shape)
            cols = len(shape[0])
            rotated = [[0 for _ in range(rows)] for _ in range(cols)]
            
            for r in range(rows):
                for c in range(cols):
                    rotated[c][rows - 1 - r] = shape[r][c]
            
            shape = rotated
        
        return shape

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris with AI Prediction")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
        self.reset_game()
        
        # AI parameters
        self.ai_active = True
        self.move_delay = 100  # Milliseconds
        self.last_move_time = 0
        
        # UI elements
        self.toggle_button_rect = pygame.Rect(0, 0, 120, 40)  # Will position in draw_info
    
    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.pause = False
        
        # Initialize bag of pieces (random bag of 7)
        self.bag = list(SHAPES.keys())
        random.shuffle(self.bag)
        self.next_pieces = deque()
        
        # Fill next pieces queue
        for _ in range(3):  # Show 3 next pieces
            if not self.bag:
                self.bag = list(SHAPES.keys())
                random.shuffle(self.bag)
            self.next_pieces.append(self.bag.pop(0))
        
        # Current piece
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        self.current_piece = Tetromino(self.bag.pop(0))
        
        # Initial fall speed (milliseconds per drop)
        self.fall_speed = 1000
        self.last_fall_time = pygame.time.get_ticks()
        
        # For soft drop
        self.soft_drop = False
        
        # For AI prediction
        self.prediction = None
    
    def update_grid_with_piece(self, piece, grid=None, commit=False):
        """
        Add the piece to the grid. If commit is False, just returns the new grid.
        If commit is True, modifies the actual game grid.
        """
        if grid is None:
            grid = [row[:] for row in self.grid]  # Make a copy
        
        shape = piece.get_rotated_shape(piece.rotation)
        
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c]:
                    if 0 <= piece.y + r < GRID_HEIGHT and 0 <= piece.x + c < GRID_WIDTH:
                        if commit:
                            self.grid[piece.y + r][piece.x + c] = piece.shape_name
                        else:
                            grid[piece.y + r][piece.x + c] = piece.shape_name
        
        return grid
    
    def is_collision(self, piece):
        """Check if the piece collides with the grid or boundaries."""
        shape = piece.get_rotated_shape(piece.rotation)
        
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c]:
                    # Check if piece is outside the grid
                    if (piece.y + r >= GRID_HEIGHT or 
                        piece.x + c < 0 or 
                        piece.x + c >= GRID_WIDTH):
                        return True
                    
                    # Check if the cell is already filled
                    if piece.y + r >= 0 and self.grid[piece.y + r][piece.x + c]:
                        return True
        
        return False
    
    def clear_lines(self):
        """Clear completed lines and return the number of lines cleared."""
        lines_to_clear = []
        
        for r in range(GRID_HEIGHT):
            if all(self.grid[r]):
                lines_to_clear.append(r)
        
        # Remove the completed rows and add new empty rows at the top
        for r in lines_to_clear:
            del self.grid[r]
            self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])
        
        # Update score and level
        num_lines = len(lines_to_clear)
        if num_lines > 0:
            self.lines_cleared += num_lines
            self.score += num_lines * 100 * self.level
            
            # Update level and fall speed
            self.level = (self.lines_cleared // 10) + 1
            self.fall_speed = max(100, 1000 - (self.level - 1) * 100)  # Speed up as level increases
        
        return num_lines
    
    def get_next_piece(self):
        """Get the next piece from the queue and add a new one to the queue."""
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        
        next_piece = Tetromino(self.next_pieces.popleft())
        self.next_pieces.append(self.bag.pop(0))
        
        return next_piece
    
    def hard_drop(self):
        """Instantly drop the piece to the lowest possible position."""
        while not self.is_collision(Tetromino(self.current_piece.shape_name, self.current_piece.x, self.current_piece.y + 1, self.current_piece.rotation)):
            self.current_piece.y += 1
        
        self.lock_piece()
    
    def lock_piece(self):
        """Lock the current piece into the grid and get the next piece."""
        self.update_grid_with_piece(self.current_piece, commit=True)
        self.clear_lines()
        
        # Get the next piece
        self.current_piece = self.get_next_piece()
        
        # Check for game over (if the new piece immediately collides)
        if self.is_collision(self.current_piece):
            self.game_over = True
    
    def ai_find_best_move(self):
        """Find the best move for the current piece using a simple heuristic."""
        best_score = float('-inf')
        best_move = None
        
        # Try all possible rotations and x positions
        for rotation in range(4):
            for x in range(-2, GRID_WIDTH + 2):  # Allow some leeway for pieces that might overlap edges
                test_piece = Tetromino(self.current_piece.shape_name, x, 0, rotation)
                
                # If this position isn't valid, skip it
                if self.is_collision(test_piece):
                    continue
                
                # Drop the piece to the bottom
                while not self.is_collision(Tetromino(test_piece.shape_name, test_piece.x, test_piece.y + 1, test_piece.rotation)):
                    test_piece.y += 1
                
                # Evaluate this position
                test_grid = self.update_grid_with_piece(test_piece)
                score = self.evaluate_position(test_grid)
                
                if score > best_score:
                    best_score = score
                    best_move = (x, rotation)
        
        return best_move
    
    def evaluate_position(self, grid):
        """
        Evaluate a potential board position using heuristics.
        Higher score is better.
        """
        # Count holes (empty cells with a filled cell above them)
        holes = 0
        for c in range(GRID_WIDTH):
            block_found = False
            for r in range(GRID_HEIGHT):
                if grid[r][c]:
                    block_found = True
                elif block_found:
                    holes += 1
        
        # Calculate aggregate height (sum of heights of each column)
        aggregate_height = 0
        for c in range(GRID_WIDTH):
            for r in range(GRID_HEIGHT):
                if grid[r][c]:
                    aggregate_height += GRID_HEIGHT - r
                    break
        
        # Count completed lines
        complete_lines = 0
        for r in range(GRID_HEIGHT):
            if all(grid[r]):
                complete_lines += 1
        
        # Count bumpiness (sum of differences between adjacent column heights)
        bumpiness = 0
        column_heights = []
        for c in range(GRID_WIDTH):
            height = 0
            for r in range(GRID_HEIGHT):
                if grid[r][c]:
                    height = GRID_HEIGHT - r
                    break
            column_heights.append(height)
        
        for i in range(len(column_heights) - 1):
            bumpiness += abs(column_heights[i] - column_heights[i + 1])
        
        # Weight the different heuristics
        return (
            complete_lines * 500 -
            holes * 100 -
            aggregate_height * 20 -
            bumpiness * 50
        )
    
    def draw_grid(self):
        """Draw the game grid."""
        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                pygame.draw.rect(
                    self.screen,
                    GRAY,
                    (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE),
                    1  # Border width
                )
                
                if self.grid[r][c]:
                    pygame.draw.rect(
                        self.screen,
                        COLORS[self.grid[r][c]],
                        (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    )
    
    def draw_piece(self, piece, alpha=255, offset_x=0, offset_y=0):
        """Draw a tetromino piece."""
        shape = piece.get_rotated_shape(piece.rotation)
        
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c]:
                    color = piece.color
                    
                    # If alpha is specified, create a transparent surface
                    if alpha < 255:
                        s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        s.fill((color[0], color[1], color[2], alpha))
                        self.screen.blit(
                            s,
                            ((piece.x + c) * CELL_SIZE + offset_x, 
                             (piece.y + r) * CELL_SIZE + offset_y)
                        )
                    else:
                        pygame.draw.rect(
                            self.screen,
                            color,
                            ((piece.x + c) * CELL_SIZE + offset_x, 
                             (piece.y + r) * CELL_SIZE + offset_y, 
                             CELL_SIZE, CELL_SIZE)
                        )
    
    def draw_prediction(self):
        """Draw the predicted best move."""
        if self.prediction:
            best_x, best_rotation = self.prediction
            
            # Create a ghost piece at the predicted position
            ghost = Tetromino(self.current_piece.shape_name, best_x, 0, best_rotation)
            
            # Drop it to the bottom
            while not self.is_collision(Tetromino(ghost.shape_name, ghost.x, ghost.y + 1, ghost.rotation)):
                ghost.y += 1
            
            # Draw the ghost piece with transparency
            self.draw_piece(ghost, alpha=128)
    
    def draw_ghost_piece(self):
        """Draw a ghost piece showing where the current piece will land."""
        ghost = Tetromino(self.current_piece.shape_name, self.current_piece.x, self.current_piece.y, self.current_piece.rotation)
        
        # Drop it to the bottom
        while not self.is_collision(Tetromino(ghost.shape_name, ghost.x, ghost.y + 1, ghost.rotation)):
            ghost.y += 1
        
        # Draw the ghost piece with transparency
        self.draw_piece(ghost, alpha=100)
    
    def draw_next_pieces(self):
        """Draw the next pieces in the queue."""
        info_x = GRID_WIDTH * CELL_SIZE + 50
        
        self.screen.blit(
            self.font.render("Next Pieces:", True, WHITE),
            (info_x, 20)
        )
        
        for i, piece_name in enumerate(self.next_pieces):
            # Create a piece object for display
            next_piece = Tetromino(piece_name)
            
            # Calculate position for the preview
            preview_x = info_x + 50
            preview_y = 70 + i * 100
            
            # Draw a background for the preview
            box_width = 120
            box_height = 90
            pygame.draw.rect(
                self.screen,
                GRAY,
                (info_x, preview_y - 10, box_width, box_height),
                1  # Border width
            )
            
            # Get piece shape and dimensions
            shape = next_piece.shape
            shape_height = len(shape) * CELL_SIZE
            shape_width = len(shape[0]) * CELL_SIZE
            
            # Calculate center position for the piece
            center_x = info_x + box_width // 2
            center_y = preview_y - 10 + box_height // 2
            
            # Calculate offset to center the piece in the box
            offset_x = center_x - (shape_width // 2)
            offset_y = center_y - (shape_height // 2)
            
            # Draw each cell of the piece
            for r in range(len(shape)):
                for c in range(len(shape[0])):
                    if shape[r][c]:
                        pygame.draw.rect(
                            self.screen,
                            next_piece.color,
                            (offset_x + c * CELL_SIZE, offset_y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        )
    
    def draw_info(self):
        """Draw game information."""
        info_x = GRID_WIDTH * CELL_SIZE + 50
        info_y = 350
        
        # Draw score
        self.screen.blit(
            self.font.render(f"Score: {self.score}", True, WHITE),
            (info_x, info_y)
        )
        
        # Draw level
        self.screen.blit(
            self.font.render(f"Level: {self.level}", True, WHITE),
            (info_x, info_y + 40)
        )
        
        # Draw lines cleared
        self.screen.blit(
            self.font.render(f"Lines: {self.lines_cleared}", True, WHITE),
            (info_x, info_y + 80)
        )
        
        # Draw AI status and toggle button
        status = "ON" if self.ai_active else "OFF"
        color = GREEN if self.ai_active else RED
        button_color = GREEN if self.ai_active else RED
        button_text = f"AI: {status}"
        
        # Position the button
        self.toggle_button_rect.x = info_x
        self.toggle_button_rect.y = info_y + 120
        
        # Draw the button
        pygame.draw.rect(self.screen, button_color, self.toggle_button_rect)
        pygame.draw.rect(self.screen, WHITE, self.toggle_button_rect, 2)  # Button border
        
        # Draw button text
        button_label = self.font.render(button_text, True, WHITE)
        text_x = self.toggle_button_rect.x + (self.toggle_button_rect.width - button_label.get_width()) // 2
        text_y = self.toggle_button_rect.y + (self.toggle_button_rect.height - button_label.get_height()) // 2
        self.screen.blit(button_label, (text_x, text_y))
        
        # Draw controls info
        controls_y = info_y + 180
        controls = [
            "Controls:",
            "Arrow Left/Right: Move",
            "Arrow Up: Rotate",
            "Arrow Down: Soft Drop",
            "Space: Hard Drop",
            "P: Pause",
            "R: Reset Game",
            "A: Toggle AI"
        ]
        
        for i, text in enumerate(controls):
            self.screen.blit(
                self.small_font.render(text, True, WHITE),
                (info_x, controls_y + i * 25)
            )
    
    def draw_game_over(self):
        """Draw game over screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = self.font.render("Press R to restart", True, WHITE)
        
        self.screen.blit(
            game_over_text,
            (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
             SCREEN_HEIGHT // 2 - 60)
        )
        
        self.screen.blit(
            score_text,
            (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 
             SCREEN_HEIGHT // 2)
        )
        
        self.screen.blit(
            restart_text,
            (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
             SCREEN_HEIGHT // 2 + 60)
        )
    
    def draw_pause(self):
        """Draw pause screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.font.render("PAUSED", True, YELLOW)
        continue_text = self.font.render("Press P to continue", True, WHITE)
        
        self.screen.blit(
            pause_text,
            (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 
             SCREEN_HEIGHT // 2 - 30)
        )
        
        self.screen.blit(
            continue_text,
            (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, 
             SCREEN_HEIGHT // 2 + 30)
        )
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if AI toggle button was clicked
                if self.toggle_button_rect.collidepoint(event.pos):
                    self.ai_active = not self.ai_active
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
                
                if self.game_over:
                    continue
                
                if event.key == pygame.K_p:
                    self.pause = not self.pause
                
                if self.pause:
                    continue
                
                if event.key == pygame.K_a:
                    self.ai_active = not self.ai_active
                
                if event.key == pygame.K_LEFT:
                    # Move piece left
                    self.current_piece.x -= 1
                    if self.is_collision(self.current_piece):
                        self.current_piece.x += 1
                
                elif event.key == pygame.K_RIGHT:
                    # Move piece right
                    self.current_piece.x += 1
                    if self.is_collision(self.current_piece):
                        self.current_piece.x -= 1
                
                elif event.key == pygame.K_DOWN:
                    # Soft drop
                    self.soft_drop = True
                
                elif event.key == pygame.K_UP:
                    # Rotate piece
                    original_rotation = self.current_piece.rotation
                    self.current_piece.rotation = (self.current_piece.rotation + 1) % 4
                    if self.is_collision(self.current_piece):
                        self.current_piece.rotation = original_rotation
                
                elif event.key == pygame.K_SPACE:
                    # Hard drop
                    self.hard_drop()
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    self.soft_drop = False
        
        return True
    
    def update(self):
        """Update game state."""
        if self.game_over or self.pause:
            return
        
        current_time = pygame.time.get_ticks()
        
        # AI move
        if self.ai_active and current_time - self.last_move_time > self.move_delay:
            self.last_move_time = current_time
            
            # Find best move
            self.prediction = self.ai_find_best_move() # TODO SEND TO API
            
            if self.prediction:
                best_x, best_rotation = self.prediction
                
                # Gradually move the piece toward the best position
                moved = False
                rotated = False
                
                # Handle rotation first
                if self.current_piece.rotation != best_rotation:
                    original_rotation = self.current_piece.rotation
                    self.current_piece.rotation = (self.current_piece.rotation + 1) % 4
                    if self.is_collision(self.current_piece):
                        self.current_piece.rotation = original_rotation
                    else:
                        rotated = True
                
                # Then handle horizontal movement if we didn't rotate
                if not rotated:
                    if self.current_piece.x < best_x:
                        self.current_piece.x += 1
                        if self.is_collision(self.current_piece):
                            self.current_piece.x -= 1
                        else:
                            moved = True
                    elif self.current_piece.x > best_x:
                        self.current_piece.x -= 1
                        if self.is_collision(self.current_piece):
                            self.current_piece.x += 1
                        else:
                            moved = True
                
                # If piece is in the right position, drop it
                if not moved and not rotated and self.current_piece.x == best_x and self.current_piece.rotation == best_rotation:
                    # Accelerate the piece's fall
                    self.last_fall_time -= self.fall_speed // 2
        
        # Piece falling
        fall_delay = self.fall_speed // 10 if self.soft_drop else self.fall_speed
        if current_time - self.last_fall_time > fall_delay:
            self.last_fall_time = current_time
            
            # Move piece down
            self.current_piece.y += 1
            if self.is_collision(self.current_piece):
                self.current_piece.y -= 1  # Undo the move
                self.lock_piece()
    
    def render(self):
        """Render the game."""
        self.screen.fill(BLACK)
        
        # Draw game elements
        self.draw_grid()
        self.draw_ghost_piece()
        self.draw_piece(self.current_piece)
        
        if self.ai_active:
            self.draw_prediction()
        
        self.draw_next_pieces()
        self.draw_info()
        
        # Draw overlays
        if self.game_over:
            self.draw_game_over()
        elif self.pause:
            self.draw_pause()
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = TetrisGame()
    game.run()

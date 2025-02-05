from random import randint

import numpy as np
import matplotlib.pyplot as plt
import pygame
import random
from collections import deque, defaultdict
import argparse

# Funkce pro výpočet distance matrix pomocí BFS
def compute_distance_matrix(matrix, seat_pos):
    # Kontrola typu seat_pos
    if not isinstance(seat_pos, tuple) or len(seat_pos) != 2:
        raise ValueError(f"seat_pos musí být tuple se dvěma prvky, ale byl předán: {seat_pos} (type: {type(seat_pos)})")

    # Kontrola platnosti seat_pos
    x, y = seat_pos
    if not (0 <= x < matrix.shape[0] and 0 <= y < matrix.shape[1]):
        raise ValueError(f"seat_pos {seat_pos} je mimo rozsah matice s tvarem {matrix.shape}")

    distance_matrix = np.full(matrix.shape, np.inf)
    queue = deque()
    queue.append((seat_pos, 0))
    distance_matrix[seat_pos] = 0
    while queue:
        current, dist = queue.popleft()
        neighbors = [
            (current[0] - 1, current[1]),
            (current[0] + 1, current[1]),
            (current[0], current[1] - 1),
            (current[0], current[1] + 1)
        ]
        for neighbor in neighbors:
            if (0 <= neighbor[0] < matrix.shape[0] and
                0 <= neighbor[1] < matrix.shape[1] and
                matrix[neighbor] != np.inf and
                distance_matrix[neighbor] > dist + 1):
                distance_matrix[neighbor] = dist + 1
                queue.append((neighbor, dist + 1))
    return distance_matrix

# Třída Airplane pro správu matice letadla
class Airplane:
    def __init__(self, seat_rows=32, seat_in_row=[3, 3], door_choice='left'):
        self.seat_rows = seat_rows
        self.seat_in_row = seat_in_row
        self.door_choice = door_choice
        self.matrix, self.door_positions, self.seat_positions = self.initialize_matrix()

    def initialize_matrix(self):
        seat_rows = self.seat_rows
        seat_in_row = self.seat_in_row
        door_choice = self.door_choice

        # Rozměry letadla
        rows = 2 * seat_rows + 1  # Počet řad v hlavní části (včetně pruhů zdí)
        aisle_count = len(seat_in_row) - 1  # Počet uliček mezi sekcemi
        cols = 2 + aisle_count + sum(seat_in_row)  # Celkový počet sloupců (sedadla + uličky + plášť)

        # Inicializace matice
        matrix = np.zeros((rows, cols))  # 0 = volné místo (bílá)

        # Každý sudý řádek je zeď (černý pruh)
        for i in range(0, rows, 2):
            matrix[i, :] = np.inf

        # Přidání černých krajních sloupců (plášť letadla)
        matrix[:, 0] = np.inf  # Levý kraj
        matrix[:, -1] = np.inf  # Pravý kraj

        # Logika pro sedadla a uličky
        current_col = 1  # Začátek za levou zdí

        for section_index, seats in enumerate(seat_in_row):
            # Přidání sedadel pro danou sekci
            for i in range(1, rows, 2):  # Sudé řádky jsou sedadla
                for s in range(seats):
                    seat_pos = (i, current_col + s)
                    matrix[seat_pos] = -3  # Sedadla označená jako -3

            # Posun za sedadla
            current_col += seats

            # Přidání uličky (pokud není poslední sekce)
            if section_index < aisle_count:
                matrix[:, current_col] = 0  # Ulička
                current_col += 1

        # Přidání řádků nahoře a dole
        top_row = np.full(cols, np.inf)  # Horní černý řádek
        bottom_row = np.full(cols, np.inf)  # Dolní černý řádek
        top_white_row = np.zeros(cols)  # Bílý řádek pod horní zdí
        bottom_white_row = np.zeros(cols)  # Bílý řádek nad dolní zdí

        # Umístění dveří na krajích bílých řádků
        top_white_row[-1] = -1  # Dveře nahoře
        bottom_white_row[-1] = -1  # Dveře dole
        top_white_row[:seat_in_row[0] + 1] = np.inf  # Zeď vlevo nahoře
        bottom_white_row[:seat_in_row[0] + 1] = np.inf  # Zeď vlevo dole

        # Spojení do finální matice
        matrix = np.vstack([top_row, top_white_row, matrix, bottom_white_row, bottom_row])

        # Transpozice matice pro otočení o 90 stupňů doleva
        matrix = matrix.T

        # Identifikace dveří po transpozici
        door_positions = []
        for j in range(matrix.shape[1]):
            for i in range(matrix.shape[0]):
                if matrix[i, j] == -1:
                    door_positions.append((i, j))

        # Výběr dveří na základě volby
        selected_doors = []
        for pos in door_positions:
            if door_choice == 'left' and pos[1] == 1:  # Levé dveře
                selected_doors.append(pos)
            elif door_choice == 'right' and pos[1] == matrix.shape[1] - 2:  # Pravé dveře
                selected_doors.append(pos)
            elif door_choice == 'both':
                selected_doors.append(pos)

        # Pokud žádné dveře nebyly nalezeny podle výběru, použijeme všechny
        if not selected_doors:
            selected_doors = door_positions.copy()

        # Identifikace seat_positions po transpozici
        seat_positions = []
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if matrix[i, j] == -3:
                    seat_positions.append((i, j))

        return matrix, selected_doors, seat_positions

# Třída Passenger pro správu jednotlivých pasažérů
class Passenger:
    def __init__(self, ped_id, spawn_pos, seat_pos, distance_matrix, baggage_probability=0.6):
        self.ped_id = ped_id
        self.current_pos = spawn_pos
        self.seat_pos = seat_pos
        self.distance_matrix = distance_matrix
        self.next_move = spawn_pos  # Inicializace next_move na spawn_pos
        self.seated = False  # Stav pasažéra

        self.desired_move = None  # a space where a passenger wants to move but can't because another passenger is standing there
        self.swapping = False
        self.swapping_speed = random.randint(1, 3)
        self.swapping_progress = None

        self.seating_in_progress = False
        self.seating_steps_remaining = 0

        # Přiřazení zavazadla s pravděpodobností
        self.has_baggage = random.random() < baggage_probability
        if self.has_baggage:
            self.baggage_steps_remaining = random.randint(1, 3)
            self.baggage_stopped = False
        else:
            self.baggage_steps_remaining = 0
            self.baggage_stopped = False

    # Slouží k vyhodnocení, zda není požadované sedadlo blokované
    # Např. pasažér sedící v uličce blokuje přístup k sedadlu u okna
    def check_blocked_seats(self, current_pos, seat_pos, seat_status):
        seat_row, seat_col = seat_pos
        current_row, current_col = current_pos

        if current_col != seat_col:
            return False, 0

        blocking_positions = []

        for row in range(min(current_row, seat_row) + 1, max(current_row, seat_row)):
            blocking_positions.append((row, seat_col))

        blocking_count = 0
        for pos in blocking_positions:
            if seat_status[pos]:
                blocking_count += 1

        return blocking_count > 0, blocking_count

    def decide_move(self, occupied_positions, blocked_passengers, seat_status):
        if self.seated:
            self.next_move = self.current_pos  # Zůstat na místě, pokud je již seated
            return

        # Pokud má zavazadlo a ještě se nezastavil, kontroluje, zda je na své sloupci
        if self.has_baggage and not self.baggage_stopped:
            _, current_col = self.current_pos
            _, target_col = self.seat_pos
            if current_col == target_col:
                # Zastaví se a začne ukládat zavazadlo
                self.baggage_stopped = True
                print(f"Passenger {self.ped_id} started storing baggage at column {current_col}")
                self.next_move = self.current_pos  # Zůstat na místě
                return  # Nechce se pohybovat

        # Pokud má zavazadlo a je v procesu ukládání
        if self.has_baggage and self.baggage_stopped and self.baggage_steps_remaining > 0:
            self.baggage_steps_remaining -= 1
            print(f"Passenger {self.ped_id} storing baggage, steps remaining: {self.baggage_steps_remaining}")
            if self.baggage_steps_remaining == 0:
                print(f"Passenger {self.ped_id} finished storing baggage")
            self.next_move = self.current_pos  # Zůstat na místě
            return  # Nechce se pohybovat

        # Pokud se usazuje -> vyměňuje se s pasažárem na blokujícím sedadle
        if self.seating_in_progress:
            self.seating_steps_remaining -= 1
            if self.seating_steps_remaining == 0:
                self.seating_in_progress = False
                self.next_move = self.seat_pos
            return

        seat_is_blocked, blocking_count = self.check_blocked_seats(self.current_pos, self.seat_pos, seat_status)
        # Pokud je sedadlo blokované, doba do usazení se odvíjí od počtu blokujících pasažérů
        if seat_is_blocked:
            self.seating_in_progress = True
            self.seating_steps_remaining = blocking_count * randint(3, 5)
            self.next_move = self.current_pos
            return

        if self.swapping:
            self.swapping_progress -= 1
            print(f"Passenger {self.ped_id} swapping, steps remaining: {self.swapping_progress}")
            if self.swapping_progress == 0:
                print(f"Passenger {self.ped_id} swapped")
                self.next_move = self.desired_move
                self.desired_move = None
                self.swapping_progress = None
                self.swapping = False
            return

        x, y = self.current_pos
        min_dist = self.distance_matrix[x, y]
        candidates = []
        # Sousední buňky (nahoru, dolů, vlevo, vpravo)
        directions = [
            (-1, 0),  # Nahoru
            (1, 0),   # Dolů
            (0, -1),  # Vlevo
            (0, 1)    # Vpravo
        ]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.distance_matrix.shape[0] and
                0 <= ny < self.distance_matrix.shape[1] and
                self.distance_matrix[nx, ny] != np.inf):
                    if self.distance_matrix[nx, ny] < min_dist:
                        if (nx, ny) in occupied_positions:
                            self.desired_move = (nx, ny)
                            blocked_passengers[self.current_pos] = self
                        else:  # if there isn't a passenger standing
                            min_dist = self.distance_matrix[nx, ny]
                            candidates = [(nx, ny)]
                    elif self.distance_matrix[nx, ny] == min_dist:
                        candidates.append((nx, ny))
        if candidates:
            self.next_move = random.choice(candidates)

            # clean-up
            if self.current_pos in blocked_passengers: del blocked_passengers[self.current_pos]
            self.desired_move = None  # the passenger moved so they aren't in a conflict
            self.swapping = False  # found a place to move so can't be swapping
        else:
            # Pokud nejsou žádni kandidáti, zůstat na místě
            print(f"Passenger {self.ped_id} has no valid moves and stays at {self.current_pos}")
            self.next_move = self.current_pos  # Zůstat na místě

    def move(self):
        if self.next_move and isinstance(self.next_move, tuple):
            self.current_pos = self.next_move
        else:
            # Pokud by se 'next_move' dostalo do 'None', zůstat na místě
            print(f"Warning: Passenger {self.ped_id} has next_move set to None or invalid. Staying in place.")

# Třída Simulation pro správu simulace a Pygame
class Simulation:
    def __init__(self, seat_rows=32, seat_in_row=[3, 3], door_choice='left',
                 baggage_probability=0.6, ticks_per_second=10,
                 seating_strategy='random'):
        # Nastavení parametrů
        self.seat_rows = seat_rows
        self.seat_in_row = seat_in_row
        self.door_choice = door_choice
        self.baggage_probability = baggage_probability
        self.ticks_per_second = ticks_per_second
        self.seating_strategy = seating_strategy
        self.passenger_seated_at = [];

        # Inicializace Airplane
        self.airplane = Airplane(seat_rows=self.seat_rows,
                                 seat_in_row=self.seat_in_row,
                                 door_choice=self.door_choice)

        self.matrix = self.airplane.matrix
        self.door_positions = self.airplane.door_positions
        self.seat_positions = self.airplane.seat_positions.copy()

        # Inicializace pasažérů
        self.available_seats = self.seat_positions.copy()

        # Řazení pasažérů do optimální podoby
        midpoint = int(np.floor(len(self.available_seats) / 2))
        self.available_seats.sort(key=lambda x: x[1])

        # Rozdělení letadla na přední a zadní část
        self.available_seats_split = [
            self.available_seats[:midpoint],  # Left half
            self.available_seats[midpoint:]  # Right half
        ]
        self.available_seats_split[0].sort(key=lambda x: (x[1], -x[0] if x[0] <= seat_in_row[0] else x[0]))
        self.available_seats_split[1].sort(key=lambda x: (-x[1], -x[0] if x[0] <= seat_in_row[0] else x[0]))

        self.passengers = []
        self.seat_status = {seat: False for seat in self.seat_positions}  # False = unoccupied
        self.ped_id_counter = 0

        # Inicializace Pygame
        pygame.init()
        aspect_ratio = self.matrix.shape[1] / self.matrix.shape[0]

        # Nastavení velikosti obrazovky a výpočet cell_size
        screen_width = 1200  # Šířka okna
        bar_height = 100      # Výška baru

        # Výpočet velikosti buňky na základě šířky okna a počtu sloupců
        self.cell_size = screen_width // self.matrix.shape[1]

        # Výpočet výšky gridu
        grid_height = self.matrix.shape[0] * self.cell_size

        # Výpočet celkové výšky okna (grid + bar)
        self.width = self.matrix.shape[1] * self.cell_size
        self.height = grid_height + bar_height

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Airplane Matrix with Passengers")

        # Barvy
        self.colors = {
            0: (255, 255, 255),  # Bílá (volné místo)
            np.inf: (0, 0, 0),    # Černá (zeď)
            -1: (0, 0, 255),     # Modrá (dveře)
            -3: (192, 192, 192), # Šedá (sedadla)
        }

        # Barvy pro pasažéry
        self.passenger_color = (255, 165, 0)  # Oranžová
        self.seated_color = (0, 255, 0)      # Zelená
        self.storing_color = (0, 255, 255)   # Azurová (pro ukládání zavazadel)
        self.seating_color = (255, 0, 0)  # Usazující se
        self.swapping_color = (255, 100, 200)  # Switching protijdouci

        # Inicializace fontů
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 20)  # Nastavení fontu a velikosti

        # Časování
        self.spawn_interval = 1000 // self.ticks_per_second  # Interval spawnu v milisekundách
        self.last_spawn_time = pygame.time.get_ticks()

    def draw_grid(self):
        for i in range(self.matrix.shape[0]):
            for j in range(self.matrix.shape[1]):
                value = self.matrix[i, j]
                color = self.colors.get(value, (255, 0, 0))  # Defaultně červená pro neznámé hodnoty
                pygame.draw.rect(self.screen, color, (j * self.cell_size, i * self.cell_size + 100, self.cell_size, self.cell_size))
                pygame.draw.rect(self.screen, (200, 200, 200), (j * self.cell_size, i * self.cell_size + 100, self.cell_size, self.cell_size), 1)

        # Vykreslení pasažérů
        for passenger in self.passengers:
            x, y = passenger.current_pos
            if passenger.seated:
                color = self.seated_color
            elif passenger.has_baggage and passenger.baggage_stopped:
                color = self.storing_color
            elif passenger.swapping:
                color = self.swapping_color
            elif passenger.seating_in_progress:
                color = self.seating_color
            else:
                color = self.passenger_color

            center_x = int(y * self.cell_size + self.cell_size / 2)
            center_y = int(x * self.cell_size + self.cell_size / 2) + 100  # Offset by 100 for the bar

            pygame.draw.circle(
                self.screen,
                color,
                (center_x, center_y),
                self.cell_size // 3
            )
            if passenger.has_baggage and passenger.baggage_steps_remaining is not 0:
                baggage_size = self.cell_size // 4
                square_x = center_x - baggage_size // 2
                square_y = center_y + self.cell_size // 4
                pygame.draw.rect(
                    self.screen,
                    (0, 0, 155),  # Baggage color
                    (square_x, square_y, baggage_size, baggage_size)
                )

            if passenger.swapping and passenger.desired_move:
                desired_x, desired_y = passenger.desired_move
                desired_center_x = int(desired_y * self.cell_size + self.cell_size / 2)
                desired_center_y = int(desired_x * self.cell_size + self.cell_size / 2) + 100

                arrow_length, arrow_width = 10, 2
                arrow_color = (0, 0, 0)

                def draw_arrowhead(start, end, color, width, length=10):
                    angle = np.arctan2(end[1] - start[1], end[0] - start[0])
                    point1 = (
                        end[0] - length * np.cos(angle - np.pi / 6),
                        end[1] - length * np.sin(angle - np.pi / 6)
                    )
                    point2 = (
                        end[0] - length * np.cos(angle + np.pi / 6),
                        end[1] - length * np.sin(angle + np.pi / 6)
                    )
                    pygame.draw.polygon(self.screen, color, [end, point1, point2])

                pygame.draw.line(
                    self.screen,
                    arrow_color,
                    (center_x, center_y),
                    (desired_center_x, desired_center_y),
                    arrow_width
                )
                draw_arrowhead((center_x, center_y), (desired_center_x, desired_center_y), arrow_color, arrow_width,
                               arrow_length)
                draw_arrowhead((desired_center_x, desired_center_y), (center_x, center_y), arrow_color, arrow_width,
                               arrow_length)

    def get_seat_by_priority(self, available_seats, seat_priority=[7, 1, 6, 2, 5, 3]):
        for priority in seat_priority:
            seats = [t for t in available_seats if t[0] == priority]
            if len(seats) != 0:
                selected_seat = random.choice(seats)
                available_seats.remove(selected_seat)  # Remove from list
                return selected_seat

    def assign_seat(self, door, seating_strategy='random'):
        if seating_strategy == 'random':
            return self.available_seats.pop(random.randrange(len(self.available_seats)))
        if seating_strategy == 'door_wise':
            if len(self.door_positions) == 1:
                return self.available_seats.pop(random.randrange(len(self.available_seats)))
            else:
                door_id = 0 if door[1] == 1 else 1
                if len(self.available_seats_split[door_id]) > 0:
                    seat_to_assign = self.available_seats_split[door_id].pop(random.randrange(len(self.available_seats_split[door_id])))
                    self.available_seats.remove(seat_to_assign)
                    return seat_to_assign
                else:
                    return None
        if seating_strategy == 'window_wise':
            return self.get_seat_by_priority(self.available_seats)
        if seating_strategy == 'optimal':
            if len(self.door_positions) == 1:
                return self.available_seats.pop(random.randrange(len(self.available_seats)))
            else:
                door_id = 0 if door[1] == 1 else 1
                if len(self.available_seats_split[door_id]) > 0:
                    seat_to_assign = self.available_seats_split[door_id].pop()
                    self.available_seats.remove(seat_to_assign)
                    return seat_to_assign
                else:
                    return None


    def spawn_passengers(self, seating_strategy):
        """
        Spawnuje pasažéry pouze tehdy, když je dveřní buňka volná.
        Pokračuje ve spawnování, dokud nejsou všichni pasažéři spawnováni.
        """
        for door in self.door_positions:
            # Zkontrolujte, zda je dveřní buňka volná (žádný pasažér momentálně není na dveřích)
            door_occupied = any(p.current_pos == door and not p.seated for p in self.passengers)
            if not door_occupied and self.available_seats:
                # Spawnujte nového pasažéra na dveřní buňku
                seat = self.assign_seat(door, seating_strategy)

                if seat is None:
                    continue

                try:
                    distance_matrix = compute_distance_matrix(self.matrix, seat)
                except ValueError as e:
                    print(f"Chyba při výpočtu distance_matrix pro sedadlo {seat}: {e}")
                    self.available_seats.append(seat)  # Vrať sedadlo zpět
                    continue  # Přeskočí tento krok a pokračuje dále
                passenger = Passenger(
                    ped_id=self.ped_id_counter,
                    spawn_pos=door,
                    seat_pos=seat,
                    distance_matrix=distance_matrix,
                    baggage_probability=self.baggage_probability
                )
                self.passengers.append(passenger)
                print(f"Spawning passenger {self.ped_id_counter} at door {door} with seat {seat}")
                self.ped_id_counter += 1

    # Dočasná funkce, slouží k testování správného fungování
    def spawn_passengers_with_exact_positions(self, seat_positions):
        if len(self.passengers) >= len(seat_positions):
            return

        door = self.door_positions[0]

        for seat in seat_positions:
            try:
                distance_matrix = compute_distance_matrix(self.matrix, seat)
            except ValueError as e:
                print(f"Error computing distance_matrix for seat {seat}: {e}")
                return

            passenger = Passenger(
                ped_id=self.ped_id_counter,
                spawn_pos=door,
                seat_pos=seat,
                distance_matrix=distance_matrix,
                baggage_probability=1
            )
            self.passengers.append(passenger)
            self.seat_status[seat] = True  # Mark seat as occupied
            print(f"Spawning Passenger {self.ped_id_counter} at {door} -> Seat {seat}")
            self.ped_id_counter += 1

    def resolve_conflicts(self, move_requests):
        """
        Řeší konflikty, kdy více pasažérů chce vstoupit do stejné buňky.
        Vybere náhodně jednoho pasažéra, který může pokračovat, ostatní zůstanou na místě.
        """
        for pos, peds in move_requests.items():
            if len(peds) > 1:
                chosen_ped = random.choice(peds)
                for ped in peds:
                    if ped != chosen_ped:
                        ped.next_move = ped.current_pos  # Zůstat na místě
                        print(f"Passenger {ped.ped_id} blocked from moving to {pos}")

    def resolve_swapping(self, blocked_passengers):
        """
        Resi konflikt typu chodec A chce jit na pozici chodce B
        a chodec B na pozici chodce A
        Kazdy chodec ma cas, ktery mu trva se vymenit - vybere nejvetsi z casu a zapocne odpocet casu prohozeni
        """
        if blocked_passengers:
            for current_pos in blocked_passengers:
                this_passenger = blocked_passengers[current_pos]
                if this_passenger.swapping: continue
                if this_passenger.desired_move in blocked_passengers:
                    other_passenger = blocked_passengers[this_passenger.desired_move]
                    if other_passenger.desired_move == current_pos:
                        assert this_passenger.desired_move == other_passenger.current_pos
                        assert other_passenger.desired_move == current_pos
                        this_passenger.swapping = True
                        other_passenger.swapping = True
                        time_to_swap = max(this_passenger.swapping_speed, other_passenger.swapping_speed)
                        this_passenger.swapping_progress = time_to_swap
                        other_passenger.swapping_progress = time_to_swap
                        print(f"Passenger {this_passenger.ped_id} is swapping with {other_passenger.ped_id} for duration: {time_to_swap}")

    def apply_moves(self):
        """
        Aplikuje schválené pohyby pasažérů.
        """
        for passenger in self.passengers:
            passenger.move()

            # Kontrola, zda pasažér dosáhl sedadla
            if passenger.current_pos == passenger.seat_pos and not passenger.seated:
                passenger.seated = True
                self.passenger_seated_at.append(pygame.time.get_ticks())
                self.seat_status[passenger.seat_pos] = True  # Mark seat as occupied
                print(f"Passenger {passenger.ped_id} seated at {passenger.seat_pos}")

    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Spawn pasažérů na dveřích, pokud uplynul spawn_interval
            if current_time - self.last_spawn_time > self.spawn_interval:
                self.spawn_passengers(self.seating_strategy)
                self.last_spawn_time = current_time

            # Rozhodování o pohybu
            occupied_positions = {p.current_pos for p in self.passengers if not p.seated}
            blocked_passengers = {}  # current_position : passenger - implemented to resolve passenger <-> passenger conflicts
            for passenger in self.passengers:
                passenger.decide_move(occupied_positions, blocked_passengers, self.seat_status)

            self.resolve_swapping(blocked_passengers)

            # Shromáždění požadavků na pohyb
            move_requests = defaultdict(list)
            for passenger in self.passengers:
                if passenger.next_move != passenger.current_pos and not passenger.seated:
                    move_requests[passenger.next_move].append(passenger)

            # Řešení konfliktů
            self.resolve_conflicts(move_requests)

            # Aplikace pohybů
            self.apply_moves()

            # Vykreslení
            self.screen.fill((0, 0, 0))
            self.draw_grid()

            # Výpočty pro text
            total_seats = len(self.seat_positions)
            total_passengers = len(self.passengers) + len(self.available_seats)
            yet_to_spawn = len(self.available_seats)
            in_simulation_not_seated = len([p for p in self.passengers if not p.seated])

            # Renderování textu
            text_total = self.font.render(f"Total Passengers: {total_passengers} | Total Seats: {total_seats}", True, (255, 255, 255))
            text_yet_to_spawn = self.font.render(f"Passengers yet to spawn: {yet_to_spawn}", True, (255, 255, 255))
            text_in_simulation = self.font.render(f"Passengers in simulation not seated: {in_simulation_not_seated}", True, (255, 255, 255))

            # Blitování textu na obrazovku (v horním baru)
            self.screen.blit(text_total, (10, 10))  # Horní levý roh
            self.screen.blit(text_yet_to_spawn, (10, 40))  # Pod total
            self.screen.blit(text_in_simulation, (10, 70))  # Pod yet_to_spawn

            pygame.display.flip()

            # Kontrola, zda jsou všichni pasažéři seated
            if not self.available_seats and all(p.seated for p in self.passengers):
                print("Všichni pasažéři byli přiřazeni a dosáhli svých sedadel.")
                running = False

            # Časování simulace
            clock.tick(self.ticks_per_second)

        pygame.quit()
        return pygame.time.get_ticks(), self.passenger_seated_at

# Funkce pro načtení konfigurace od uživatele
def get_user_configuration():
    parser = argparse.ArgumentParser(description="Airplane Passenger Simulation Parameters")
    parser.add_argument('--seat_rows', type=int, default=5, help='Number of seat rows in the airplane')
    parser.add_argument('--seat_in_row', type=int, nargs='+', default=[3, 3],
                        help='Number of seats in each section (e.g., 3 3)')
    parser.add_argument('--door_choice', type=str, choices=['left', 'right', 'both'], default='both',
                        help='Choice of door(s) for passenger spawning')
    parser.add_argument('--baggage_probability', type=float, default=0.6,
                        help='Probability that a passenger has baggage (0.0 - 1.0)')
    parser.add_argument('--ticks_per_second', type=int, default=5,
                        help='Number of simulation ticks (frames) per second')
    parser.add_argument('--seating_strategy', type=str, choices=['random', 'door_wise', 'window_wise', 'optimal'], default='optimal',
                        help='Seating strategy')
    args = parser.parse_args()
    return args

# Hlavní vstupní bod
if __name__ == "__main__":
    # Načtení konfigurace
    args = get_user_configuration()

    random.seed(42)
    np.random.seed(42)

    # Vytvoření a spuštění simulace
    simulation = Simulation(
        seat_rows=args.seat_rows,
        seat_in_row=args.seat_in_row,
        door_choice=args.door_choice,
        baggage_probability=args.baggage_probability,
        ticks_per_second=args.ticks_per_second,
        seating_strategy=args.seating_strategy
    )
    time_to_finish, passenger_seated_at = simulation.run()
    print(f'Simulace ukončena po {time_to_finish} krocích.')

    # Zobrazení grafu
    num_passengers = list(range(1, len(passenger_seated_at) + 1))
    plt.figure(figsize=(8, 5))
    plt.plot(passenger_seated_at, num_passengers, marker='o', linestyle='-', linewidth=2, color='b')
    plt.xlabel("Čas [ticks]")
    plt.ylabel("Počet usazených pasažérů")
    plt.title("Usazování pasažérů v čase")
    plt.grid(True)
    plt.show()

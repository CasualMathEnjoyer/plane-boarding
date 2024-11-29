# plane-boarding
colaboration project modeling boarding of a plane

# Michal - Simulace Pasažérů při Nástupu do Letadla - (1 dveře, ukládání zavazadel, usednutí na místo)

## Funkce

- **Dynamická Simulace Nástupu**: Pasažéři jsou spawnováni na vybraných dveřích (vybere uživatel) a pohybují se směrem ke svým přiřazeným sedadlům.
- **Manipulace se Zavazadly**: Pasažéři mohou mít zavazadla s pravděpodobností (p=0.6), která potřebují uložit před usednutím na sedadlo. Čas uložení se sampluje ze uniformního rozdělení na celých číslech (3,5) 
- **Řešení Konfliktů**: Simulace zvládá situace, kdy více pasažérů chce vstoupit do stejné buňky, dle kódu z přednášky.
- **Přizpůsobitelné Parametry**: Umožňuje nastavení počtu řad sedadel, počtu sedadel v každé sekci, volby dveří pro spawnování pasažérů, pravděpodobnosti, že pasažér má zavazadlo, a rychlosti simulace. Matice letadla se pak generuje adaptivně na základě prvních dvou zmíněných parametrů.
- **Vizualizace v reálném čase**: Vizualizace procesu nástupu pomocí Pygame, zobrazující pasažéry, sedadla, uličky a dveře.
- **Progress Bar**: Zobrazuje informace o celkovém počtu pasažérů, sedadel, pasažérů čekajících na spawnování a pasažérů aktuálně v simulaci.

## Jak To Funguje

### 1. Třída `Airplane`

- **Účel**: Spravuje matici letadla, včetně uspořádání sedadel, zdí a dveří.
- **Inicializace**: Nastavuje parametry letadla a vytváří matici reprezentující rozložení letadla.
- **Matice Letadla**: Používá NumPy matici k reprezentaci uspořádání, kde různé hodnoty odpovídají zdí, uličkám, sedadlům a dveřím.

### 2. Třída `Passenger`

- **Účel**: Reprezentuje jednotlivého pasažéra v simulaci.
- **Atributy**:
  - `ped_id`: Jedinečné ID pasažéra.
  - `current_pos`: Aktuální pozice pasažéra v matici.
  - `seat_pos`: Přiřazená pozice sedadla.
  - `has_baggage`: Informace o tom, zda pasažér má zavazadlo.
  - `baggage_steps_remaining`: Počet kroků potřebných k uložení zavazadla.
  - `seated`: Stav, zda je pasažér již usazen.
- **Logika Pohybu**:
  - Pasažéři se rozhodují o svém dalším kroku na základě nejkratší cesty k sedadlu.
  - Pokud má pasažér zavazadlo, zastaví se a uloží ho před pokračováním k sedadlu.
  - Konfliktní situace jsou řešeny tak, že pouze jeden pasažér může vstoupit do konkurenční buňky najednou.

### 3. Třída `Simulation`

- **Účel**: Řídí celou simulaci, včetně inicializace letadla, pasažérů a vizualizace pomocí Pygame.
- **Inicializace**: Nastavuje prostředí simulace, včetně rozměrů okna Pygame, barev, fontů a časování.
- **Metody**:
  - `draw_grid`: Vykresluje matici letadla a pasažéry na obrazovce.
  - `spawn_passengers`: Spawnuje nové pasažéry na dveřích, pokud jsou buňky dveří volné a jsou k dispozici sedadla.
  - `resolve_conflicts`: Řeší konflikty, kdy více pasažérů chce vstoupit do stejné buňky, tím, že náhodně vybere jednoho, který může pokračovat.
  - `run`: Hlavní smyčka simulace, která zpracovává události, spawnuje pasažéry, aktualizuje jejich pohyb, vykresluje scénu a kontroluje ukončení simulace.

### 4. Funkce `compute_distance_matrix`

- **Účel**: Vypočítává matici vzdáleností od každé buňky v letadle ke konkrétnímu sedadlu pomocí algoritmu Breadth-First Search (BFS).
- **Parametry**:
  - `matrix`: Matice reprezentující uspořádání letadla (zdí, uliček, sedadel).
  - `seat_pos`: Pozice cílového sedadla.
- **Výstup**: Matice vzdáleností, kde každá buňka obsahuje minimální počet kroků potřebných k dosažení cílového sedadla.

## Vizualizace

- **Okno Pygame**: Zobrazuje horní bar s informacemi o simulaci a samotný grid letadla, kde různé barvy reprezentují různé prvky (zdi, uličky, sedadla, dveře, pasažéry).
- **Pasažéři**:
  - **Oranžová**: Aktivní pasažéři, kteří se pohybují k sedadlům.
  - **Zelená**: Usazení pasažéři.
  - **Azurová**: Pasažéři ukládající zavazadla.

## Ukončení Simulace

Simulace se ukončí, když jsou všichni pasažéři spawnováni a usazeni na svých sedadlech.
